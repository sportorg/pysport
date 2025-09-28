from typing import List, Tuple

import pytest

from sportorg.common.otime import OTime
from sportorg.models.memory import (
    Course,
    Group,
    Person,
    Race,
    ResultSportident,
    ResultStatus,
    Split,
    create,
    new_event,
    race,
)
from sportorg.models.result.result_checker import ResultChecker
from sportorg.utils.time import hhmmss_to_time

# Settings calculation time.
# credit_time_enabled [bool] - is enabled calculation credit time
# credit_time_сp [int] - number control point for credit time


@pytest.fixture
def new_race():
    course = create(Course)
    group = create(Group, course=course)
    person = create(Person, group=group)
    result = ResultSportident()
    result.person = person
    new_event([create(Race)])
    race().courses.append(course)
    race().groups.append(group)
    race().persons.append(person)
    race().results.append(result)
    race().set_setting("credit_time_cp", 41)

    return race


@pytest.fixture
def new_split1() -> List[Split]:
    return make_split(
        [
            ("31", "01:00:00"),
            ["41", "01:02:35"],
            ["51", "02:03:35"],
            ["41", "03:01:35"],
        ]
    )


@pytest.fixture
def new_split2() -> List[Split]:
    return make_split(
        [
            ("31", "12:03:00"),
            ["41", "13:04:35"],
            ["51", "14:02:35"],
            ["41", "15:02:35"],
        ]
    )


def make_split(splits: List[Tuple[str, str]]) -> List[Split]:
    return [
        create(Split, code=str(code), time=hhmmss_to_time(time))
        for code, time in splits
    ]


def test_credit_calculation_when_credit_time_disabled(
    new_race: Race, new_split1, new_split2
):
    race().set_setting("credit_time_enabled", False)
    ok(new_split1, expected_result=OTime())
    ok(new_split2, expected_result=OTime())


def test_credit_calculation_when_credit_time_enabled(
    new_race: Race, new_split1, new_split2
):
    race().set_setting("credit_time_enabled", True)
    ok(new_split1, expected_result=hhmmss_to_time("01:00:35"))
    ok(new_split2, expected_result=hhmmss_to_time("02:01:35"))


def ok(
    splits: List[Split],
    expected_result: OTime,
):
    result = race().results[0]
    result.splits = splits

    result.status = ResultStatus.OK
    ResultChecker.checking(result)
    result_credit = result.get_credit_time()
    assert result_credit == expected_result
