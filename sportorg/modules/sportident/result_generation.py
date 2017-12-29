import logging

from sportorg.modules.printing.model import split_printout, NoResultToPrintException, NoPrinterSelectedException
from sportorg.gui.global_access import GlobalAccess
from sportorg.models.result.result_checker import ResultChecker, ResultCheckerException
from sportorg.models.memory import race, Person, Result, ResultSportident


class ResultSportidentGeneration:
    def __init__(self, result: ResultSportident):
        assert result, Result
        self._result = result
        self._person = None
        self.assign_chip_reading = race().get_setting('sportident_assign_chip_reading', 'off')
        self.repeated_reading = race().get_setting('sportident_repeated_reading', 'rewrite')

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
            pass  # bib
        self._add_result()

    def check_splits(self):
        if self._find_person_by_result():
            return ResultChecker(self._person).check_result(self._result)
        return False

    def _no_person(self):
        if self.assign_chip_reading == 'off':
            self._add_result_to_race()
        elif self.assign_chip_reading == 'only_unknown_members':
            # bib
            self._add_result()

    def _add_result(self):
        if isinstance(self._result.person, Person):
            self._find_person_by_result()
            try:
                ResultChecker.checking(self._result)
            except ResultCheckerException as e:
                logging.error(str(e))

            self._add_result_to_race()

            logging.info('Sportident {}'.format(self._result))
            logging.debug(self._result.status)
            GlobalAccess().auto_save()

            if race().get_setting('split_printout', False):
                try:
                    split_printout(self._result)
                except NoResultToPrintException as e:
                    logging.error(str(e))
                except NoPrinterSelectedException as e:
                    logging.error(str(e))
                except Exception as e:
                    logging.error(str(e))
        else:
            if self._find_person_by_result():
                self._result.person = self._person
                self._add_result()
            else:
                self._no_person()
