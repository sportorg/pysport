from abc import abstractmethod

from sportorg.app.models.memory import Result, race
from sportorg.core.final import Base


class ResultObject(Base):

    def __init__(self, result: Result):
        assert result, Result
        self._result = result
        self._person = None

    def _add_result_to_race(self):
        race().add_result(self._result)

    def _has_result(self):
        for result in race().results:
            if result is None:
                continue
            if result == self._result:
                return True
        return False

    def _no_person(self):
        self._add_result_to_race()

    @abstractmethod
    def add_result(self):
        pass
