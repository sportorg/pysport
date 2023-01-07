from typing import List
from sportorg.models.memory import ResultSportident, Person, Course, CourseControl, Split


def make_course(course: List[int]) -> Course:
    course_object = Course()
    course_object.controls = [make_course_control(code) for code in course]
    return course_object

def make_course_control(code: int) -> CourseControl:
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

def check(course: List[int], splits: List[int]) -> bool:
    result = make_result(splits)
    course_object = make_course(course)
    return result.check(course_object)

def correct(course: List[int], splits: List[int]) -> bool:
    return check(course, splits)

def incorrect(course: List[int], splits: List[int]) -> bool:
    return not check(course, splits)


def test_advanced_check():
    assert correct(course=[31, 32, 33],
                   splits=[31, 32, 33])

    assert incorrect(course=[31, 32, 33],
                     splits=[31, 32])
