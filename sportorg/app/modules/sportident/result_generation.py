import logging

from sportorg.app.gui.dialogs.bib_dialog import BibDialog
from sportorg.app.gui.global_access import GlobalAccess
from sportorg.app.models.memory import race, Person
from sportorg.app.models.result.result_checker import ResultChecker
from sportorg.app.models.result.result_object import ResultObject
from sportorg.app.models.result.split_calculation import split_printout


class ResultSportidentGeneration(ResultObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assign_chip_reading = race().get_setting('sportident_assign_chip_reading', 'off')
        self.repeated_reading = race().get_setting('sportident_repeated_reading', 'rewrite')

    def _find_person_by_result(self):
        if self._person is not None:
            return True
        for person in race().persons:
            if person.sportident_card is not None and person.sportident_card == self._result.sportident_card:
                self._person = person
                return True

        return False

    def _has_sportident_card(self):
        for result in race().results:
            if result is None:
                continue
            if result.sportident_card == self._result.sportident_card:
                return True
        return False

    def add_result(self):
        if self._has_result():
            return
        if self.assign_chip_reading == 'always':
            self.bib_dialog()
        self._add_result()

    def check_punches(self):
        if self._find_person_by_result():
            return ResultChecker(self._person).check_result(self._result)
        return False

    def _no_person(self):
        if self.assign_chip_reading == 'off':
            self._add_result_to_race()
        elif self.assign_chip_reading == 'only_unknown_members':
            self.bib_dialog()
            self._add_result()

    def bib_dialog(self):
        try:
            bib_dialog = BibDialog()
            bib_dialog.exec()
            self._person = bib_dialog.get_person()
        except Exception as e:
            logging.exception(str(e))

    def _add_result(self):
        if isinstance(self._result.person, Person):
            self._find_person_by_result()
            ResultChecker.checking(self._result)

            self._add_result_to_race()

            logging.info('Sportident {}'.format(self._result))
            logging.debug(self._result.status)
            GlobalAccess().auto_save()

            if race().get_setting('split_printout', False):
                split_printout(self._result)
        else:
            if self._find_person_by_result():
                self._result.person = self._person
                self._add_result()
            else:
                self._no_person()
