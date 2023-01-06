from sportorg.models.result.result_checker import ResultChecker
from sportorg.models.memory import ResultSportident, Person


def test_basic_check():
    result = ResultSportident()
    result.person = Person()
    assert ResultChecker.checking(result)
