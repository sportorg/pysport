from typing import List, Tuple, Union

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
    assert ok(course=[31, 32, "33"], splits=[31, 32, 33], penalty=0)
    assert dsq(course=[31, 32, "33"], splits=[31, 32, 70], penalty=0)


def ok(
    course: List[Union[int, str]],
    splits: List[int],
    result_status: ResultStatus = ResultStatus.OK,
    penalty: int = 0,
) -> bool:
    """Проверка отметки: результат засчитан, начислено заданное количество штрафа

    Parameters
    ----------
    course : List[Union[int, str]]
        Порядок прохождения дистанции
    splits : List[int]
        Отметки спортсмена на дистанции
    result_status: ResultStatus,
        Ожидаемый результат проверки. По умолчанию result_status=ResultStatus.OK
    penalty : int
        Ожидаемое количество штрафа. Минуты или штрафные круги — зависит от
        заранее заданных настроек.

    Returns
    -------
    bool
        Возвращает True если отметка признана правильной и штраф совпадает
    """
    return all(check(course, splits, result_status=result_status, penalty=penalty))


def dsq(
    course: List[Union[int, str]],
    splits: List[int],
    result_status: ResultStatus = ResultStatus.MISSING_PUNCH,
    penalty: int = 0,
) -> bool:
    """Проверка отметки: результат не засчитан, нарушение порядка прохождения
    дистанции, но штраф посчитан верно.

    Parameters
    ----------
    course : List[Union[int, str]]
        Порядок прохождения дистанции
    splits : List[int]
        Отметки спортсмена на дистанции
    result_status: ResultStatus,
        Ожидаемый результат проверки. По умолчанию result_status=ResultStatus.MISSING_PUNCH
    penalty : int
        Ожидаемое количество штрафа. Минуты или штрафные круги — зависит от
        заранее заданных настроек.

    Returns
    -------
    bool
        Возвращает True если отметка признана неправильной, но штраф посчитан верно
    """
    return all(check(course, splits, result_status=result_status, penalty=penalty))


def check(
    course: List[Union[int, str]],
    splits: List[int],
    result_status: ResultStatus = ResultStatus.OK,
    penalty: int = 0,
) -> Tuple[bool, bool]:
    """Проверка отметки с начислением штрафа. Параметры проверки задаются
    заранее и хранятся в объекте race().get_setings().

    Parameters
    ----------
    course : List[Union[int, str]]
        Порядок прохождения дистанции
    splits : List[int]
        Отметки спортсмена на дистанции
    result_status: ResultStatus,
        Ожидаемый результат проверки. По умолчанию result_status=ResultStatus.OK
    penalty : int
        Ожидаемое количество штрафа. Минуты или штрафные круги — зависит от
        заранее заданных настроек. По умолчанию penalty=0

    Returns
    -------
    Tuple[bool, bool]
        Возвращает кортеж: результат проверки правильности прохождения и
        результат сравнения начисленного штрафа с ожидаемым.
    """
    race().courses[0].controls = make_course_controls(course)
    result = race().results[0]
    result.splits = make_splits(splits)
    ResultChecker.checking(result)
    return result.status == result_status, result.penalty_laps == penalty


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
    control.update_data({"code": code, "length": 0})
    return control


def make_splits(splits: List[int]) -> List[Split]:
    return [create(Split, code=str(code)) for code in splits]
