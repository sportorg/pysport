"""Penalty calculation tests for marked-route and free-order scenarios.

Settings covered in this suite:
- marked_route_mode: off | time | laps
- marked_route_penalty_time: default 60000 ms
- marked_route_if_counting_lap: default True
- marked_route_if_station_check: default False
- marked_route_penalty_lap_station_code: default 80
- marked_route_dont_dsq: default False
- marked_route_max_penalty_by_cp: default False
"""

from itertools import zip_longest
from typing import List, Tuple, Union

from sportorg.models.memory import (
    Course,
    CourseControl,
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


def test_basic_syntax():
    create_race()

    race().set_setting("marked_route_mode", "laps")
    assert ok(course=[31, "41", "51(51,52)"], splits=[31, 41, 51], penalty=0)
    assert ok(course=[31, "41", "51(51,52)"], splits=[31, 41, 52], penalty=1)
    assert dsq(course=[31, "41", "51(51,52)"], splits=[31, 41, 59], penalty=0)

    race().set_setting("marked_route_mode", "time")
    assert ok(course=[31, "41", "51(51,52)"], splits=[31, 41, 51], penalty=0)
    assert ok(course=[31, "41", "51(51,52)"], splits=[31, 41, 52], penalty=1)
    assert dsq(course=[31, "41", "51(51,52)"], splits=[31, 41, 59], penalty=0)


def test_marked_route_yes_no():
    """Check YES/NO marked-route behavior and penalty assignment."""
    # fmt: off
    create_race()
    race().set_setting('marked_route_mode', 'time')

    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31,          41,          51,         100], penalty=0)

    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31,          42,          51,         100], penalty=1)

    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 32,          42,          52,         100], penalty=3)

    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31, 31,      41,          51,         100], penalty=0)

    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31,          41,          52, 52,     100], penalty=1)

    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 32, 31,      41,          51,         100], penalty=1)

    assert dsq(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31,                       51,         100], penalty=0)

    assert dsq(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31,          41,          51,            ], penalty=0)

    assert dsq(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[                                          ], penalty=0)

    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31, 75,      41,          51,         100], penalty=0)

    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31, 75,      41,          51,         100], penalty=0)

    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 70, 71, 72, 73,   31, 41, 51,         100], penalty=0)

    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 40, 41, 42, 43,   31, 41, 51,         100], penalty=1)
    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 40, 41, 42, 43,   31, 42, 51,         100], penalty=1)
    # fmt: on


def test_penalty_calculation_function():
    """Verify documented `penalty_calculation` examples."""
    # fmt: off
    create_race()
    race().set_setting('marked_route_mode', 'time')

    # return quantity of incorrect or duplicated punches, order is ignored
    # origin: 31,41,51; athlete: 31,41,51; result:0
    assert  ok(course=[31, 41, 51],
               splits=[31, 41, 51], penalty=0)

    # origin: 31,41,51; athlete: 31; result:2
    assert dsq(course=[31, 41, 51],
               splits=[31,       ], penalty=2)

    # origin: 31,41,51; athlete: 41,31,51; result:2
    assert dsq(course=[31, 41, 51],
               splits=[41, 31, 51], penalty=2)

    # origin: 31,41,51; athlete: 41,31,51; result:2
    assert dsq(course=[31, 41, 51],
               splits=[41, 31, 51], penalty=2)

    # origin: 31,41,51; athlete: 31,42,51; result:2
    assert dsq(course=[31, 41, 51],
               splits=[31, 42, 51], penalty=2)

    # origin: 31,41,51; athlete: 31,41,51,52; result:1
    assert  ok(course=[31, 41, 51],
               splits=[31, 41, 51, 52], penalty=1)

    # origin: 31,41,51; athlete: 31,42,51,52; result:3
    assert dsq(course=[31, 41, 51],
               splits=[31, 42, 51, 52], penalty=3)

    # origin: 31,41,51; athlete: 31,31,41,51; result:0
    assert  ok(course=[31, 41, 51],
               splits=[31, 31, 41, 51], penalty=0)

    # origin: 31,41,51; athlete: 31,41,51,51; result:0
    assert  ok(course=[31, 41, 51],
               splits=[31, 41, 51, 51], penalty=0)

    # origin: 31,41,51; athlete: 32,42,52; result:6
    assert dsq(course=[31, 41, 51],
               splits=[32, 42, 52], penalty=6)

    # origin: 31,41,51; athlete: 31,41,51,61,71,81,91; result:4
    assert  ok(course=[31, 41, 51],
               splits=[31, 41, 51, 61, 71, 81, 91], penalty=4)

    # origin: 31,41,51; athlete: 31,41,52,61,71,81,91; result:6
    assert dsq(course=[31, 41, 51],
               splits=[31, 41, 52, 61, 71, 81, 91], penalty=6)

    # origin: 31,41,51; athlete: 51,61,71,81,91,31,41; result:6
    assert dsq(course=[31, 41, 51],
               splits=[51, 61, 71, 81, 91, 31, 41], penalty=6)

    # origin: 31,41,51; athlete: 51,61,71,81,91,32,41; result:8
    assert dsq(course=[31, 41, 51],
               splits=[51, 61, 71, 81, 91, 32, 41], penalty=8)

    # origin: 31,41,51; athlete: 51,61,71,81,91,32,42; result:8
    assert dsq(course=[31, 41, 51],
               splits=[51, 61, 71, 81, 91, 32, 42], penalty=8)

    # origin: 31,41,51; athlete: 52,61,71,81,91,32,42; result:10
    assert dsq(course=[31, 41, 51],
               splits=[52, 61, 71, 81, 91, 32, 42], penalty=10)

    # origin: 31,41,51; athlete: no punches; result:3
    assert dsq(course=[31, 41, 51],
               splits=[], penalty=3)

    # wildcard support for free order
    # origin: *,*,* athlete: 31; result:2
    assert dsq(course=['*', '*', '*'],
               splits=[31], penalty=2)

    # origin: *,*,* athlete: 31,31; result:2
    assert dsq(course=['*', '*', '*'],
               splits=[31, 31], penalty=2)

    # origin: *,*,* athlete: 31,31,31,31; result:2
    assert dsq(course=['*', '*', '*'],
               splits=[31, 31, 31, 31], penalty=2)
    # fmt: on


def test_non_obvious_behavior():
    """Document current behavior for edge cases in penalty calculation."""
    create_race()
    race().set_setting("marked_route_mode", "laps")

    assert dsq(course=["31", "41(41,42)"], splits=[31], penalty=0)
    assert dsq(course=["31", "41(41,42)"], splits=[41], penalty=0)
    assert dsq(course=["31", "41(41,42)"], splits=[39, 41], penalty=0)
    assert dsq(course=["31", "41(41,42)"], splits=[31, 49], penalty=0)

    assert ok(course=["31", "41"], splits=[31, 77, 41], penalty=1)
    assert ok(course=["31", "41(41,42)"], splits=[31, 77, 41], penalty=0)


def ok(
    course: List[Union[int, str]],
    splits: List[int],
    result_status: ResultStatus = ResultStatus.OK,
    penalty: int = 0,
) -> bool:
    """Return True when status and penalty match expected successful result."""
    return all(check(course, splits, result_status=result_status, penalty=penalty))


def dsq(
    course: List[Union[int, str]],
    splits: List[int],
    result_status: ResultStatus = ResultStatus.MISSING_PUNCH,
    penalty: int = 0,
) -> bool:
    """Return True when status and penalty match expected disqualification."""
    return all(check(course, splits, result_status=result_status, penalty=penalty))


def check(
    course: List[Union[int, str]],
    splits: List[int],
    result_status: ResultStatus = ResultStatus.OK,
    penalty: int = 0,
) -> Tuple[bool, bool]:
    """Run result checking and validate both status and penalty."""
    race().courses[0].controls = make_course_controls(course)
    result = race().results[0]
    result.splits = make_splits(splits)
    ResultChecker.checking(result)
    result_penalty = get_penalty(result)

    check_result = result.status == result_status, result_penalty == penalty

    if not all(check_result):
        message = exception_message(
            course=course,
            splits=splits,
            result_status_expected=result_status,
            result_status_received=result.status,
            penalty_expected=penalty,
            penalty_received=result_penalty,
        )
        raise ValueError(message)

    return check_result


def create_race():
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


def make_course(course: List[Union[int, str]]) -> Course:
    course_object = Course()
    course_object.controls = make_course_controls(course)
    return course_object


def make_course_controls(course: List[Union[int, str]]) -> List[CourseControl]:
    return [make_course_control(code) for code in course]


def make_course_control(code: Union[int, str]) -> CourseControl:
    control = CourseControl()
    control.update_data({"code": code, "length": 0})
    return control


def make_splits(splits: List[int]) -> List[Split]:
    return [create(Split, code=str(code)) for code in splits]


def get_penalty(result: ResultSportident) -> int:
    marked_route_mode = race().get_setting("marked_route_mode", "off")
    if marked_route_mode == "laps":
        return result.penalty_laps
    elif marked_route_mode == "time":
        penalty_time = race().get_setting("marked_route_penalty_time", 60000)
        if result.penalty_time:
            return result.penalty_time.to_msec() / penalty_time

    return 0


def exception_message(
    course: List[Union[int, str]],
    splits: List[int],
    result_status_expected: ResultStatus,
    result_status_received: ResultStatus,
    penalty_expected: int,
    penalty_received: int,
) -> str:
    """Build an assertion message with received and expected values."""
    message = "Check failed"
    message += "\n" + split_and_course_repr(course, splits)
    if result_status_expected != result_status_received:
        message += "\n" + "Result status failed!"
        message += "\n" + f"Expected: {result_status_expected}"
        message += "\n" + f"Received: {result_status_received}"
    if penalty_expected != penalty_received:
        message += "\n" + "Penalty failed!"
        message += "\n" + f"Expected: {penalty_expected}"
        message += "\n" + f"Received: {penalty_received}"
    return message


def split_and_course_repr(course: List[Union[int, str]], splits: List[int]) -> str:
    """Render splits and course rows for readable debug output."""
    spl = splits
    crs = course
    return "\n".join([f"{s:3}  {c}" for s, c in zip_longest(spl, crs, fillvalue="")])
