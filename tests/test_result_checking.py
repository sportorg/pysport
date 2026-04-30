from itertools import zip_longest
from typing import List, Union

import pytest

from sportorg.common.otime import OTime
from sportorg.models.memory import (
    Course,
    CourseControl,
    Group,
    Person,
    Race,
    RaceType,
    ResultSportident,
    ResultStatus,
    Split,
    create,
    new_event,
    race,
    set_current_race_index,
)
from sportorg.models.result.result_checker import ResultChecker


def test_controls_as_int():
    assert ok(course=[31, 32, 33], splits=[31, 32, 33])

    assert dsq(course=[31, 32, 33], splits=[])


def test_controls_as_str():
    assert ok(course=["31", "32", "33"], splits=[31, 32, 33])

    assert dsq(course=["31", "32", "33"], splits=[])


def test_controls_with_optional_codes():
    assert ok(course=["31(31,32,33)"], splits=[31])
    assert ok(course=["31(31,32,33)"], splits=[32])
    assert dsq(course=["31(31,32,33)"], splits=[70])

    assert dsq(course=["31(41,42,43)"], splits=[31])
    assert ok(course=["31(41,42,43)"], splits=[41])

    course_object = make_course(["31(31,32,33)"])
    result = make_result([31])
    assert result.check(course_object)
    assert result.splits[0].code == "31"
    assert result.splits[0].is_correct
    assert not result.splits[0].has_penalty

    course_object = make_course(["31(31,32,33)"])
    result = make_result([32])
    assert result.check(course_object)
    assert result.splits[0].code == "32"
    assert result.splits[0].is_correct
    assert result.splits[0].has_penalty

    course_object = make_course(["31(31,32,33)"])
    result = make_result([70])
    assert not result.check(course_object)
    assert result.splits[0].code == "70"
    assert not result.splits[0].is_correct
    assert result.splits[0].has_penalty


def test_controls_with_optional_code_ranges():
    course = ["31(31-33)"]
    assert ok(course, splits=[31])
    assert ok(course, splits=[32])
    assert ok(course, splits=[33])
    assert dsq(course, splits=[34])

    course = ["31(31,41-43,51,61-64)"]
    assert ok(course, splits=[31])
    assert ok(course, splits=[41])
    assert ok(course, splits=[42])
    assert ok(course, splits=[43])
    assert ok(course, splits=[51])
    assert ok(course, splits=[61])
    assert ok(course, splits=[62])
    assert ok(course, splits=[63])
    assert dsq(course, splits=[32])
    assert dsq(course, splits=[44])
    assert dsq(course, splits=[60])
    assert dsq(course, splits=[65])


def test_free_course_order_unique_controls():
    """Check free-order templates with unique wildcard controls."""
    assert ok(course=["*"], splits=[31])
    assert ok(course=["*"], splits=[71])

    assert ok(course=["*(31,32,33)"], splits=[31])
    assert ok(course=["*(31,32,33)"], splits=[32])
    assert dsq(course=["*(31,32,33)"], splits=[34])

    course = ["*", "*", "*"]
    assert ok(course, splits=[31, 32, 33])
    assert ok(course, splits=[31, 32, 33, 34])
    assert ok(course, splits=[31, 32, 31, 33])
    assert dsq(course, splits=[31, 32, 31])
    assert dsq(course, splits=[31, 32])

    course = ["*(31-33)", "*(41-43)", "*(51-53)", "*"]
    assert ok(course, splits=[31, 41, 51, 32])
    assert ok(course, splits=[31, 42, 53, 32])
    assert dsq(course, splits=[31, 42, 53, 31])

    course = [31, "*", "*(31-33)"]
    assert ok(course, splits=[31, 32, 33])
    assert ok(course, splits=[31, 31, 33])
    assert dsq(course, splits=[31, 33, 33])


def test_free_course_order_any_controls():
    assert ok(course=["%"], splits=[31])
    assert ok(course=["%"], splits=[71])

    assert ok(course=["%(31,32,33)"], splits=[31])
    assert ok(course=["%(31,32,33)"], splits=[32])
    assert dsq(course=["%(31,32,33)"], splits=[34])

    course = ["%", "%", "%"]
    assert ok(course, splits=[31, 32, 33])
    assert ok(course, splits=[31, 32, 33, 34])
    assert ok(course, splits=[31, 32, 31, 33])
    assert ok(course, splits=[31, 32, 31])
    assert ok(course, splits=[31, 31, 31])
    assert dsq(course, splits=[31, 32])

    course = (["%(31-33)", "%(41-43)", "%(51-53)", "%"],)
    assert ok(course, splits=[31, 41, 51, 32])
    assert ok(course, splits=[31, 42, 53, 32])
    assert ok(course, splits=[31, 42, 53, 31])

    course = [31, "%", "%(31-33)"]
    assert ok(course, splits=[31, 32, 33])
    assert ok(course, splits=[31, 31, 31])

    course = [31, "*", "*", "%", "%"]
    assert ok(course, splits=[31, 32, 33, 34, 35])
    assert ok(course, splits=[31, 31, 32, 31, 31])
    assert dsq(course, splits=[31, 32, 32, 34, 35])
    course = [31, "%", "%", "*", "*"]
    assert ok(course, splits=[31, 31, 31, 31, 32])


@pytest.mark.parametrize(
    "course,splits",
    [
        (["31*", "31*", "31*"], [51, 61, 71]),
        (["31%", "31%", "31%"], [51, 51, 51]),
    ],
)
def test_penalty_calculation_supports_suffix_free_order_templates(course, splits):
    course_object = make_course(course)
    result = make_result(splits)
    assert result.check(course_object)
    assert ResultChecker.penalty_calculation(result.splits, course_object.controls) == 0


def test_get_number_code_blank_string():
    control = make_course_control("   ")
    assert control.get_number_code() == "0"


def test_course_pre_ordered():
    """Check a fixed-order course where split order must match."""
    assert ok(course=[31, 32, 33], splits=[31, 32, 33])

    assert ok(course=[31, 32, 33], splits=[99, 31, 32, 33])

    assert ok(course=[31, 32, 33], splits=[31, 99, 32, 33])

    assert ok(course=[31, 32, 33], splits=[31, 32, 33, 99])

    assert dsq(course=[31, 32, 33], splits=[32, 33])

    assert dsq(course=[31, 32, 33], splits=[31, 33])

    assert dsq(course=[31, 32, 33], splits=[31, 32])

    assert dsq(course=[31, 32, 33], splits=[99, 32, 33])

    assert dsq(course=[31, 32, 33], splits=[51, 99, 33])

    assert dsq(course=[31, 32, 33], splits=[31, 32, 99])

    assert dsq(course=[31, 32, 33], splits=[31, 33, 32])


def test_course_free_order():
    """Check score/free-order style courses with mixed constraints."""

    c = ["*", "*", "*"]
    assert ok(c, [31, 32, 33])
    assert ok(c, [71, 72, 73])
    assert ok(c, [31, 32, 33, 34])
    assert dsq(c, [31, 32])
    assert dsq(c, [31, 31, 33])
    assert dsq(c, [31, 32, 32])
    assert dsq(c, [31, 32, 31])

    c = ["*(31,32,33,34)", "*(31,32,33,34)", "*(31,32,33,34)"]
    assert ok(c, [31, 32, 33])
    assert ok(c, [31, 31, 32, 33])

    assert dsq(c, [31, 32, 73])
    assert dsq(c, [31, 32, 31])
    assert dsq(c, [31, 32])

    c = ["*(31,32,33,34)", "*(31,32,33,34)", "*(71,72,73,74)", "*(71,72,73,74)"]
    assert ok(c, [31, 34, 71, 74])
    assert ok(c, [31, 31, 34, 71, 74])
    assert ok(c, [31, 47, 34, 71, 74])
    assert ok(c, [31, 32, 34, 71, 74])
    assert ok(c, [31, 32, 71, 72, 74])

    assert dsq(c, [31, 71, 34, 74])
    assert dsq(c, [31, 34, 74])
    assert dsq(c, [31, 44, 71, 74])
    assert dsq(c, [31, 34, 41, 74])

    c = ["31", "*(32,33,34)", "*(32,33,34)", "70"]
    assert ok(c, [31, 32, 33, 70])
    assert ok(c, [31, 31, 32, 33, 70])
    assert ok(c, [31, 32, 33, 70, 71])
    assert ok(c, [31, 32, 33, 34, 70])

    assert dsq(c, [71, 32, 33, 70])
    assert dsq(c, [31, 32, 33, 71])
    assert dsq(c, [31, 32, 73, 70])
    assert dsq(c, [31, 32, 32, 70])
    assert dsq(c, [32, 33, 70])
    assert dsq(c, [31, 32, 70])
    assert dsq(c, [31, 32, 33])

    c = ["*(31,32,33)", "55", "*(31,32,33)"]
    assert ok(c, [31, 55, 33])
    assert ok(c, [31, 32, 55, 33])
    assert ok(c, [31, 55, 33, 31])
    assert ok(c, [71, 31, 55, 33])

    assert dsq(c, [31, 55, 31])
    assert dsq(c, [71, 55, 33])
    assert dsq(c, [31, 75, 33])
    assert dsq(c, [31, 55, 73])
    assert dsq(c, [55, 33])
    assert dsq(c, [31, 33])
    assert dsq(c, [31, 55])

    c = [31, "*(33,34,35)", "*(33,34,35)", 39, 41, "*(43,44,45)", "*(43,44,45)", 49]
    assert ok(c, [31, 33, 34, 39, 41, 45, 43, 49])
    assert ok(c, [31, 33, 34, 39, 71, 41, 45, 43, 49])


def test_course_butterfly():
    """Check butterfly forking patterns."""
    c = [31, 32, "*(41,51)", "*(42,52)", 32, "*(51,41)", "*(52,42)", 32, 39]
    assert ok(c, [31, 32, 41, 42, 32, 51, 52, 32, 39])
    assert ok(c, [31, 32, 51, 52, 32, 41, 42, 32, 39])

    assert ok(c, [70, 31, 32, 41, 42, 32, 51, 52, 32, 39])
    assert ok(c, [31, 32, 41, 70, 42, 32, 51, 52, 32, 39])
    assert ok(c, [31, 32, 41, 42, 32, 51, 52, 32, 39, 70])

    assert dsq(c, [31, 32, 41, 42, 32, 41, 42, 32, 39])
    assert dsq(c, [31, 32, 51, 52, 35, 51, 52, 32, 39])
    assert dsq(c, [32, 41, 42, 32, 51, 52, 32, 39])
    assert dsq(c, [31, 32, 41, 42, 32, 51, 52, 32])
    assert dsq(c, [31, 32, 42, 32, 51, 52, 32, 39])
    assert dsq(c, [31, 32, 41, 42, 51, 52, 32, 39])
    assert dsq(c, [70, 32, 41, 42, 32, 51, 52, 32, 39])
    assert dsq(c, [31, 32, 41, 42, 32, 51, 52, 32, 70])
    assert dsq(c, [31, 32, 70, 42, 32, 51, 52, 32, 39])
    assert dsq(c, [31, 32, 41, 42, 70, 51, 52, 32, 39])

    c = [31, 32, "*(41,51)", 33, 32, "*(51,41)", 33, 39]
    assert ok(c, [31, 32, 41, 33, 32, 51, 33, 39])
    assert ok(c, [31, 32, 51, 33, 32, 41, 33, 39])

    assert ok(c, [70, 31, 32, 41, 33, 32, 51, 33, 39])
    assert ok(c, [31, 32, 41, 70, 33, 32, 51, 33, 39])
    assert ok(c, [31, 32, 41, 33, 32, 51, 33, 39, 70])

    assert dsq(c, [31, 32, 41, 33, 32, 41, 33, 39])
    assert dsq(c, [31, 41, 32, 33, 32, 51, 33, 39])
    assert dsq(c, [31, 32, 41, 51, 33, 32, 33, 39])
    assert dsq(c, [32, 41, 33, 32, 51, 33, 39])
    assert dsq(c, [31, 32, 33, 32, 51, 33, 39])
    assert dsq(c, [31, 32, 41, 33, 32, 51, 33])
    assert dsq(c, [70, 32, 41, 33, 32, 51, 33, 39])
    assert dsq(c, [31, 32, 70, 33, 32, 51, 33, 39])
    assert dsq(c, [31, 32, 41, 33, 32, 51, 33, 70])

    c = [
        31,
        32,
        "*(41,51)",
        "*(42,52)",
        "*(43,32)",
        "*(32,41)",
        "*(51,42)",
        "*(52,43)",
        32,
        39,
    ]
    assert ok(c, [31, 32, 41, 42, 43, 32, 51, 52, 32, 39])
    assert ok(c, [31, 32, 51, 52, 32, 41, 42, 43, 32, 39])

    assert ok(c, [70, 31, 32, 41, 42, 43, 32, 51, 52, 32, 39])
    assert ok(c, [31, 32, 41, 42, 70, 43, 32, 51, 52, 32, 39])
    assert ok(c, [31, 32, 41, 42, 43, 32, 51, 52, 32, 39, 70])

    assert dsq(c, [31, 32, 41, 42, 43, 32, 41, 42, 43, 32, 39])
    assert dsq(c, [31, 32, 51, 52, 32, 51, 52, 32, 39])
    assert dsq(c, [32, 41, 42, 43, 32, 51, 52, 32, 39])
    assert dsq(c, [31, 32, 41, 43, 32, 51, 52, 32, 39])
    assert dsq(c, [31, 32, 41, 42, 43, 51, 52, 32, 39])
    assert dsq(c, [31, 32, 41, 42, 43, 32, 51, 52, 32])
    assert dsq(c, [70, 32, 41, 42, 43, 32, 51, 52, 32, 39])
    assert dsq(c, [31, 32, 41, 70, 43, 32, 51, 52, 32, 39])
    assert dsq(c, [31, 32, 41, 42, 43, 70, 51, 52, 32, 39])
    assert dsq(c, [31, 32, 41, 42, 43, 32, 51, 52, 32, 70])

    c = [31, 32, "*(41,51)", "*(42,33)", "*(33,32)", "*(32,41)", "*(51,42)", 33, 39]
    assert ok(c, [31, 32, 41, 42, 33, 32, 51, 33, 39])
    assert ok(c, [31, 32, 51, 33, 32, 41, 42, 33, 39])

    assert ok(c, [70, 31, 32, 41, 42, 33, 32, 51, 33, 39])
    assert ok(c, [31, 32, 41, 42, 70, 33, 32, 51, 33, 39])
    assert ok(c, [31, 32, 41, 42, 33, 32, 51, 33, 39, 70])

    assert dsq(c, [31, 32, 41, 42, 33, 32, 41, 42, 33, 39])
    assert dsq(c, [31, 32, 51, 33, 32, 51, 33, 39])
    assert dsq(c, [32, 41, 42, 33, 32, 51, 33, 39])
    assert dsq(c, [31, 32, 41, 42, 32, 51, 33, 39])
    assert dsq(c, [31, 32, 41, 42, 33, 32, 51, 33])
    assert dsq(c, [70, 32, 41, 42, 33, 32, 51, 33, 39])
    assert dsq(c, [31, 32, 41, 42, 70, 32, 51, 33, 39])
    assert dsq(c, [31, 32, 41, 42, 33, 32, 51, 33, 70])


@pytest.mark.parametrize(
    "controls, expected",
    [
        ([], 0),
        ([31, 32, 33, 34], 12),
        ([11, 22, 33, 44], 10),
        ([31, 999, 34], 105),
        ([31, 31, 33, 31, 33], 6),
    ],
)
def test_calculate_rogaine_score(controls, expected):
    create_race()
    race().set_setting("result_processing_score_mode", "rogain")  # wrong spelling
    res = make_result(controls)
    assert ResultChecker.calculate_rogaine_score(res) == expected


@pytest.mark.parametrize(
    "fixed_value, controls, expected",
    [
        (1, [], 0),
        (1, [31, 32, 33, 34], 4),
        (2, [31, 32, 33, 34], 8),
        (1, [11, 22, 33, 44], 4),
        (1, [31, 999, 34], 3),
        (1, [31, 31, 33, 31, 33], 2),
    ],
)
def test_calculate_fixed_score(fixed_value, controls, expected):
    create_race()
    race().set_setting("result_processing_score_mode", "fixed")
    race().set_setting("result_processing_fixed_score_value", fixed_value)
    res = make_result(controls)
    assert ResultChecker.calculate_rogaine_score(res) == expected


@pytest.mark.parametrize(
    "score_mode, controls, expected",
    [
        ("rogain", [], 0),
        ("rogain", [31, 31], 6),
        ("rogain", [31, 32, 33, 34], 12),
        ("rogain", [31, 31, 33, 31, 33], 15),
        ("rogain", [11, 22, 33, 44], 10),
        ("rogain", [11, 22, 33, 22, 44], 12),
        ("fixed", [], 0),
        ("fixed", [31, 31], 2),
        ("fixed", [31, 32, 33, 34], 4),
        ("fixed", [31, 31, 33, 31, 33], 5),
        ("fixed", [11, 22, 33, 44], 4),
        ("fixed", [11, 22, 33, 22, 44], 5),
    ],
)
def test_calculate_score_allow_duplicates(score_mode, controls, expected):
    create_race()
    race().set_setting("result_processing_score_mode", score_mode)
    race().set_setting("result_processing_fixed_score_value", 1)
    res = make_result(controls)
    assert ResultChecker.calculate_rogaine_score(res, allow_duplicates=True) == expected


# fmt: off
@pytest.mark.parametrize(
    'step, score, max_time, finish, expected',
    [
        (1, 5, (0, 1, 0, 0), (0, 0, 59, 59), 0),
        (1, 5, (0, 1, 0, 0), (0, 1,  0,  0), 0),
        (1, 5, (0, 1, 0, 0), (0, 1,  0,  1), 1),
        (1, 5, (0, 1, 0, 0), (0, 1,  0, 30), 1),
        (1, 5, (0, 1, 0, 0), (0, 1,  1,  0), 1),
        (1, 5, (0, 1, 0, 0), (0, 1,  1,  1), 2),
        (1, 5, (0, 1, 0, 0), (0, 1,  5,  1), 5),
        (1, 5, (0, 1, 0, 0), (0, 1,  6,  1), 5), # penalty does not exceed total score
        (1, 5, (0, 1, 0, 0), (0, 1, 15,  1), 5), # penalty does not exceed total score
    ],
)
# fmt: on
def test_calculate_rogaine_penalty(step, score, max_time, finish, expected):
    create_race()
    race().set_setting('result_processing_scores_minute_penalty', 1)
    race().groups[0].max_time = OTime(*max_time)
    result = race().results[0]
    result.finish_time = OTime(*finish)
    assert ResultChecker.calculate_rogaine_penalty(result, score, step) == expected


def test_non_obvious_behavior():
    """Document edge cases that may look surprising but are currently expected."""
    c = [31, '*', '*', 34]
    assert ok(c, [31, 31, 33, 34])
    assert ok(c, [31, 32, 34, 34])
    c = [31, '*(31,32,33,34)', '*(31,32,33,34)', 34]
    assert ok(c, [31, 31, 33, 34])
    assert ok(c, [31, 32, 34, 34])

    c = ['*(31,32,50)', '*(31,32,50)', 90, '*(50,71,72)', '*(50,71,72)']
    assert dsq(c, [31, 50, 90, 71, 50])

    c = [31, 32, '*(33,35)', '*(34,36)', 32, '*(33,35)', '*(34,36)', 32, 37]
    assert ok(c, [31, 32, 33, 36, 32, 35, 34, 32, 37])

    # 1) 31 -32- -41-42-43- -32- -51-52-    -32- 39
    # 2) 31 -32- -51-52-    -32- -41-42-43- -32- 39
    c = [
        31,
        32,
        '*(41,51)',
        '*(42,52)',
        '*(43,32)',
        '*(32,41)',
        '*(51,42)',
        '*(52,43)',
        32,
        39,
    ]
    assert dsq(c, [31, 32, 41, 42, 32, 43, 32, 51, 52, 32, 39])

    course = ['31(41,42,43)']
    assert dsq(course, splits=[31])
    assert ok(course, splits=[41])

    result = make_result([31])
    assert not result.check(make_course(course))
    assert not result.splits[0].is_correct
    assert result.splits[0].has_penalty

    result = make_result([41])
    assert result.check(make_course(course))
    assert result.splits[0].is_correct
    assert result.splits[0].has_penalty


def ok(course: List[Union[int, str]], splits: List[int]) -> bool:
    """Return True when the course is accepted for the given splits."""
    return check(course, splits, True)


def dsq(course: List[Union[int, str]], splits: List[int]) -> bool:
    """Return True when the course is rejected for the given splits."""
    return not check(course, splits, False)


def check(
    course: List[Union[int, str]], splits: List[int], expected: bool = True
) -> bool:
    """Validate check outcome and raise a detailed error on mismatch."""
    result = make_result(splits)
    course_object = make_course(course)
    check_result = result.check(course_object)

    if check_result != expected:
        message = exception_message(
            course=course,
            splits=splits,
            check_result_expected=expected,
            check_result_received=check_result,
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
    set_current_race_index(0)
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
    control.update_data({'code': code, 'length': 0})
    return control


def make_result(splits: List[int]) -> ResultSportident:
    result = ResultSportident()
    result.person = Person()
    result.splits = [make_split_control(code) for code in splits]
    return result


def make_split_control(code: int) -> Split:
    split = Split()
    split.update_data({'code': code, 'time': 0})
    return split


def exception_message(
    course: List[Union[int, str]],
    splits: List[int],
    check_result_expected: bool,
    check_result_received: bool,
) -> str:
    """Build an assertion message with side-by-side course/split details."""
    message = 'Check failed'
    message += '\n' + split_and_course_repr(course, splits)
    if check_result_expected != check_result_received:
        message += '\n' + 'Result status failed!'
        message += '\n' + f'Expected: {check_result_expected}'
        message += '\n' + f'Received: {check_result_received}'
    return message


def split_and_course_repr(course: List[Union[int, str]], splits: List[int]) -> str:
    """Render splits and course rows for readable diff-style debugging."""
    spl = splits
    crs = course
    return '\n'.join([f'{s:3}  {c}' for s, c in zip_longest(spl, crs, fillvalue='')])


def test_overtime_multi_day_race_current_day_exceeds_max_time():
    course = create(Course)

    # Day 1 — current race, 45 min result
    group1 = create(Group, course=course)
    group1.name = "M21"
    group1.race_type = RaceType.INDIVIDUAL_RACE
    person1 = create(Person, group=group1)
    person1.name = "Athlete"
    person1.start_time = OTime(0, 10, 0, 0)
    result1 = ResultSportident()
    result1.person = person1
    result1.finish_time = OTime(0, 10, 45, 0)
    day1 = create(Race)
    day1.groups.append(group1)
    day1.persons.append(person1)
    day1.results.append(result1)

    # Day 2 — same athlete (matched by multi_day_id), 65 min result
    group2 = create(Group, course=course)
    group2.name = "M21"
    group2.race_type = RaceType.MULTI_DAY_RACE
    group2.max_time = OTime(0, 1, 0, 0)
    person2 = create(Person, group=group2)
    person2.name = "Athlete"
    person2.start_time = OTime(0, 10, 0, 0)
    result2 = ResultSportident()
    result2.person = person2
    result2.finish_time = OTime(0, 11, 5, 0)
    day2 = create(Race)
    day2.groups.append(group2)
    day2.persons.append(person2)
    day2.results.append(result2)

    new_event([day1, day2])
    set_current_race_index(1) # day2 is current (index 1)

    ResultChecker.check_overtime(result2)

    assert result2.status == ResultStatus.OVERTIME


def test_overtime_multi_day_race_current_day_within_max_time():
    """MULTI_DAY_RACE: OK when today's time is within max_time.

    Cumulative result (45 + 55 = 100 min) exceeds max_time (60 min),
    but only the current-day time (55 min) should be compared.
    """
    course = create(Course)

    # Day 1 — current race, 45 min result
    group1 = create(Group, course=course)
    group1.name = "M21"
    group1.race_type = RaceType.INDIVIDUAL_RACE
    person1 = create(Person, group=group1)
    person1.name = "Athlete"
    person1.start_time = OTime(0, 10, 0, 0)
    result1 = ResultSportident()
    result1.person = person1
    result1.finish_time = OTime(0, 10, 45, 0)
    day1 = create(Race)
    day1.groups.append(group1)
    day1.persons.append(person1)
    day1.results.append(result1)

    # Day 2 — same athlete (matched by multi_day_id), 55 min result
    group2 = create(Group, course=course)
    group2.name = "M21"
    group2.race_type = RaceType.MULTI_DAY_RACE
    group2.max_time = OTime(0, 1, 0, 0)
    person2 = create(Person, group=group2)
    person2.name = "Athlete"
    person2.start_time = OTime(0, 10, 0, 0)
    result2 = ResultSportident()
    result2.person = person2
    result2.finish_time = OTime(0, 10, 55, 0)
    day2 = create(Race)
    day2.groups.append(group2)
    day2.persons.append(person2)
    day2.results.append(result2)

    new_event([day1, day2])
    set_current_race_index(1) # day2 is current (index 1)

    ResultChecker.check_overtime(result2)

    assert result2.status == ResultStatus.OK


def test_overtime_individual_race_exceeds_max_time():
    create_race()
    group = race().groups[0]
    result = race().results[0]
    group.max_time = OTime(0, 1, 0, 0)
    result.person.start_time = OTime(0, 10, 0, 0)
    result.finish_time = OTime(0, 11, 5, 0)  # 65 min > 60 min

    ResultChecker.check_overtime(result)

    assert result.status == ResultStatus.OVERTIME


def test_overtime_individual_race_within_max_time():
    create_race()
    group = race().groups[0]
    result = race().results[0]
    group.max_time = OTime(0, 1, 0, 0)
    result.person.start_time = OTime(0, 10, 0, 0)
    result.finish_time = OTime(0, 10, 55, 0)  # 55 min < 60 min

    ResultChecker.check_overtime(result)

    assert result.status == ResultStatus.OK
