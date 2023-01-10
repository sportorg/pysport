from typing import List, Union

from sportorg.models.memory import (
    Course,
    CourseControl,
    Group,
    Person,
    ResultSportident,
    ResultStatus,
    Split,
    create,
    race,
)
from sportorg.models.result.result_checker import ResultChecker


def test_playground():
    create_race()
    assert ok(course=[31, 32, '33'], splits=[31, 32, 33], penalty=0)
    assert dsq(course=[31, 32, '33'], splits=[31, 32, 70], penalty=0)


def ok(course: List[Union[int, str]], splits: List[int], penalty: int) -> bool:
    '''Проверка отметки: результат засчитан

    Parameters
    ----------
    course : List[Union[int, str]]
        Порядок прохождения дистанции
    splits : List[int]
        Отметки спортсмена на дистанции

    Returns
    -------
    bool
        Возвращает True если отметка признана правильной
    '''
    return check(course, splits, penalty)

def dsq(course: List[Union[int, str]], splits: List[int], penalty: int) -> bool:
    '''Проверка отметки: результат не засчитан, нарушение порядка прохождения дистанции

    Parameters
    ----------
    course : List[Union[int, str]]
        Порядок прохождения дистанции
    splits : List[int]
        Отметки спортсмена на дистанции

    Returns
    -------
    bool
        Возвращает True если отметка признана неправильной
    '''
    return not check(course, splits, penalty)

def check(course: List[Union[int, str]], splits: List[int], penalty: int) -> bool:
    race().courses[0].controls = make_course_controls(course)
    result = race().results[0]
    result.splits = make_splits(splits)
    ResultChecker.checking(result)
    return result.status == ResultStatus.OK and result.penalty_laps == penalty

def create_race():
    course = create(Course)
    group = create(Group, course=course)
    person = create(Person, group=group)
    result = ResultSportident()
    result.person = person
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

def make_splits(splits: List[int]) -> List[Split]:
    return [create(Split, code=str(code)) for code in splits]
