from typing import List
from sportorg.models.result.result_checker import ResultChecker
from sportorg.models.memory import ResultSportident, Person, Course, CourseControl, Split


def test_basic_check():
    result = ResultSportident()
    result.person = Person()
    assert ResultChecker.checking(result)


def make_course(course) -> Course:
    course_object = Course()
    course_object.controls = [course_control(code) for code in course]
    return course_object

def course_control(code: int) -> CourseControl:
    control_object = CourseControl()
    control_object.update_data({'code': code, 'length': 0})
    return control_object

def make_result(split) -> ResultSportident:
    result = ResultSportident()
    result.person = Person()
    result.splits = [split_control(code) for code in split]
    return result

def split_control(code: int) -> Split:
    split_object = Split()
    split_object.update_data({'code': code, 'time': 0})
    return split_object

def check(course: List, split: List) -> bool:
    result = make_result(split)
    course_object = make_course(course)

    return result.check(course_object)


def test_advanced_check():
    course = [31, 32, 33]
    split = [31, 32, 33]
    assert check(course, split)
