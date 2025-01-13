import logging
from copy import deepcopy
from datetime import datetime
from enum import Enum

from sportorg.common.otime import OTime
from sportorg.gui.dialogs.bib_dialog import BibDialog
from sportorg.language import translate
from sportorg.models.memory import Person, ResultSportident, ResultStatus, race
from sportorg.models.result.result_checker import ResultChecker, ResultCheckerException
from sportorg.utils.time import time_to_otime


class FinishSource(Enum):
    station = 0
    zero = 1
    readout = 2
    dsq = 3
    penalty = 4
    cp = 5
    beam = 6


class ResultSportidentGeneration:
    def __init__(self, result: ResultSportident):
        self._result = result
        self._person = None
        self.assign_chip_reading = race().get_setting(
            "system_assign_chip_reading", "off"
        )
        self.duplicate_chip_processing = race().get_setting(
            "system_duplicate_chip_processing", "several_results"
        )
        self.card_read_repeated = self.duplicate_chip_processing == "bib_request"
        self.missed_finish = FinishSource[
            race().get_setting("system_missed_finish", "zero")
        ]
        self.finish_source = FinishSource[
            race().get_setting("system_finish_source", "station")
        ]
        self._process_missed_finish()

    def _process_missed_finish(self):
        if self._result and self._result.finish_time is None:
            if self.finish_source == FinishSource.station:
                if self.missed_finish == FinishSource.readout:
                    self._result.finish_time = time_to_otime(
                        datetime.fromtimestamp(self._result.created_at)
                    )
                elif self.missed_finish == FinishSource.zero:
                    self._result.finish_time = OTime(msec=0)
                elif self.missed_finish == FinishSource.dsq:
                    self._result.finish_time = OTime(msec=0)
                    self._result.status = ResultStatus.DISQUALIFIED
                elif self.missed_finish == FinishSource.penalty:
                    if len(self._result.splits) > 0:
                        last_cp_time = self._result.splits[-1].time
                        penalty_time = OTime(
                            msec=race().get_setting("marked_route_penalty_time", 60000)
                        )
                        self._result.finish_time = last_cp_time + penalty_time
                    else:
                        self._result.finish_time = OTime(msec=0)

    def _add_result_to_race(self):
        race().add_result(self._result)

    def _compare_result(self, result):
        eq = self._result.card_number == result.card_number
        if not eq:
            return False
        if self._result.start_time and result.start_time:
            eq = eq and self._result.start_time == result.start_time
        if self._result.finish_time and result.finish_time:
            eq = eq and self._result.finish_time == result.finish_time
        else:
            return False
        if len(self._result.splits) == len(result.splits):
            for i in range(len(self._result.splits)):
                eq = eq and self._result.splits[i].code == result.splits[i].code
                eq = eq and self._result.splits[i].time == result.splits[i].time
        else:
            return False
        return eq

    def _has_result(self):
        for result in race().results:
            if result is None:
                continue
            if self._compare_result(result):
                return True
        return False

    def _find_person_by_result(self):
        if self._person:
            return True
        for person in race().persons:
            if person.card_number and person.card_number == self._result.card_number:
                self._person = person
                return True

        return False

    def _has_sportident_card(self):
        for result in race().results:
            if result is None:
                continue
            if result.card_number == self._result.card_number:
                return True
        return False

    def _bib_dialog(self):
        try:
            bib_dialog = BibDialog("{}".format(self._result.card_number))
            bib_dialog.exec_()
            self._person = bib_dialog.get_person()
            if not self._person:
                self.assign_chip_reading = "off"
                self.card_read_repeated = False
        except Exception as e:
            logging.error(str(e))

    def _relay_find_leg(self):
        if self._find_person_by_result():
            bib = self._person.bib % 1000

            while True:
                bib += 1000
                next_leg = race().find_person_by_bib(bib)
                if next_leg:
                    next_leg_res = race().find_person_result(next_leg)
                    if not next_leg_res:
                        self._person = next_leg
                        self._result.person = next_leg
                        logging.info(
                            "Relay: Card {} assigned to bib {}".format(
                                self._result.card_number, bib
                            )
                        )
                        break
                else:
                    # All legs of relay team finished
                    break

        if not self._person:
            self.assign_chip_reading = "off"
            self.card_read_repeated = False

    def _merge_punches(self):
        card_number = self._result.card_number
        existing_res = race().find_person_by_card(card_number)

        if not existing_res:
            self._add_result()
            return True
        else:
            if existing_res.merge_with(self._result):
                # existing result changed, recalculate group results and printout
                self._result = existing_res
                ResultChecker.checking(self._result)
                self.popup_result(self._result)

            return True

    def popup_result(self, result):
        arr = race().results
        arr.remove(result)
        arr.insert(0, result)

    def add_result(self):
        if self._has_result():
            logging.info("Result already exist")
            # Comment next line to allow duplicates during readout
            return False

        if self.assign_chip_reading == "autocreate":
            # generate new person
            self._create_person()
        elif self.assign_chip_reading == "always":
            self._bib_dialog()
        elif self._has_sportident_card():
            if self.duplicate_chip_processing == "bib_request":
                self._bib_dialog()
            elif (
                self.duplicate_chip_processing == "relay_find_leg" and race().is_relay()
            ):
                self._relay_find_leg()  # assign chip to the next unfinished leg of a relay team
            elif self.duplicate_chip_processing == "merge":
                return self._merge_punches()

        self._add_result()
        return True

    def get_result(self):
        return self._result

    def _no_person(self):
        if self.assign_chip_reading == "off":
            self._add_result_to_race()
        elif self.assign_chip_reading == "only_unknown_members":
            self._bib_dialog()
            self._add_result()

    def _add_result(self):
        if isinstance(self._result.person, Person):
            self._find_person_by_result()
            try:
                ResultChecker.checking(self._result)
            except ResultCheckerException as e:
                logging.error(str(e))

            self._add_result_to_race()

            logging.info(
                "{} {}".format(self._result.system_type, self._result.card_number)
            )
        else:
            if self._find_person_by_result():
                self._result.person = self._person
                race().person_card_number(self._person, self._result.card_number)
                self._add_result()
            else:
                self._no_person()

    def _create_person(self):
        new_person = Person()
        new_person.set_bib(self._get_max_bib() + 1)
        existing_person = race().find_person_by_card(self._result.card_number)
        if existing_person:
            new_person_copy = deepcopy(existing_person)
            new_person_copy.id = new_person.id
            new_person_copy.set_bib(new_person.bib)
            new_person = new_person_copy
            new_person.set_card_number(0)
        else:
            new_person.surname = translate("Competitor") + " #" + str(new_person.bib)

        new_person.group = self._find_group_by_punches()
        self._result.person = new_person

        race().persons.append(new_person)

    def _get_max_bib(self):
        max_bib = 0
        for i in race().persons:
            max_bib = max(max_bib, i.bib)
        return max_bib

    def _find_group_by_punches(self):
        for i in race().groups:
            if i.course:
                if self._result.check(i.course):
                    return i

        if len(race().groups) > 0:
            return race().groups[0]

        return None
