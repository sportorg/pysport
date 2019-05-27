import logging

from sportorg.gui.dialogs.bib_dialog import BibDialog
from sportorg.models.result.result_checker import ResultChecker, ResultCheckerException
from sportorg.models.memory import race, Person, Result, ResultSportident
from sportorg.language import _

class ResultSportidentGeneration:
    def __init__(self, result: ResultSportident):
        assert result, Result
        self._result = result
        self._person = None
        self.assign_chip_reading = race().get_setting('system_assign_chip_reading', 'off')
        self.card_read_repeated = race().get_setting('system_card_read_repeated', False)

    def _add_result_to_race(self):
        race().add_result(self._result)

    def _has_result(self):
        for result in race().results:
            if result is None:
                continue
            if result == self._result:
                return True
        return False

    def _find_person_by_result(self):
        if self._person is not None:
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
            bib_dialog = BibDialog('{}'.format(self._result.card_number))
            bib_dialog.exec_()
            self._person = bib_dialog.get_person()
            if not self._person:
                self.assign_chip_reading = 'off'
                self.card_read_repeated = False
        except Exception as e:
            logging.error(str(e))

    def add_result(self):
        if self._has_result():
            logging.info('Result already exist')
            return False

        if self.assign_chip_reading == 'autocreate':
            # generate new person
            self._create_person()
        elif self.assign_chip_reading == 'always':
            self._bib_dialog()
        elif self.card_read_repeated and self._has_sportident_card():
            self._bib_dialog()
        self._add_result()
        return True

    def _no_person(self):
        if self.assign_chip_reading == 'off':
            self._add_result_to_race()
        elif self.assign_chip_reading == 'only_unknown_members':
            self._bib_dialog()
            self._add_result()

    def _add_result(self):
        if isinstance(self._result.person, Person):
            self._find_person_by_result()
            try:
                ResultChecker.calculate_penalty(self._result)
                ResultChecker.checking(self._result)
            except ResultCheckerException as e:
                logging.error(str(e))

            self._add_result_to_race()

            logging.info('{} {}'.format(self._result.system_type, self._result.card_number))
        else:
            if self._find_person_by_result():
                self._result.person = self._person
                race().person_card_number(self._person, self._result.card_number)
                self._add_result()
            else:
                self._no_person()

    def _create_person(self):
        new_person = Person()
        new_person.bib = self._get_max_bib() + 1
        new_person.surname = _('Competitor') + ' #' + str(new_person.bib)
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
