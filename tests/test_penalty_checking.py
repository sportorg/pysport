from typing import List, Union

from sportorg.models.memory import (
    Course,
    CourseControl,
    Group,
    Person,
    ResultSportident,
    Split,
    create,
    race,
)
from sportorg.models.result.result_checker import ResultChecker


def make_course_control(code: Union[int, str]) -> CourseControl:
    control = CourseControl()
    control.update_data({'code': code, 'length': 0})
    return control

def make_course(course: List[Union[int, str]]) -> Course:
    course_object = Course()
    course_object.controls = [make_course_control(code) for code in course]
    return course_object

def test_playground():
    course_controls = [31, 32, '33']
    result_controls = [31, 32, 33]
    course = make_course(course_controls)
    group = create(Group, course=course)
    person = create(Person, group=group)
    splits = [create(Split, code=str(code)) for code in result_controls]
    result = ResultSportident()
    result.person = person
    result.splits = splits

    r = race()
    r.courses.append(course)
    r.groups.append(group)
    r.persons.append(person)
    r.results.append(result)

    assert ResultChecker.checking(result)
