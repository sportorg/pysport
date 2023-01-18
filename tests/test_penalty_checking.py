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


def test_basic_syntax():
    create_race()

    race().set_setting('marked_route_mode', 'laps')
    assert ok(course=[31, '41', '51(51,52)'], splits=[31, 41, 51], penalty=0)
    assert ok(course=[31, '41', '51(51,52)'], splits=[31, 41, 52], penalty=1)
    assert dsq(course=[31, '41', '51(51,52)'], splits=[31, 41, 59], penalty=0)

    race().set_setting('marked_route_mode', 'time')
    assert ok(course=[31, '41', '51(51,52)'], splits=[31, 41, 51], penalty=0)
    assert ok(course=[31, '41', '51(51,52)'], splits=[31, 41, 52], penalty=1)
    assert dsq(course=[31, '41', '51(51,52)'], splits=[31, 41, 59], penalty=0)


def test_non_obvious_behavior():
    '''Неочевидное поведение при проверке дистанции. Не всегда это некорректная работа
    алгоритма, иногда может возникать из-за недочётов при составлении курсов.
    '''
    create_race()
    race().set_setting('marked_route_mode', 'laps')

    # Различие в обработке двух случаев. Тестовый случай:
    # 1) Спортсмен пропустил нужный КП -> получает штраф
    # 2) Спортсмен пропустил нужный КП, но отметился на чужом -> нет штрфа
    # Должен быть одинаковый штраф. Или начисляться за каждый лишний КП.
    # Но лишние отметки в чипе не должны уменьшать количество штрафа.
    # Да, по результатам проверки спортсмен снят. Но его могут восстановить
    # решением судьи, а штрафные круги он уже пробежал.
    assert dsq(course=['31', '41(41,42)'], splits=[31], penalty=1)
    assert dsq(course=['31', '41(41,42)'], splits=[41], penalty=1)
    assert dsq(course=['31', '41(41,42)'], splits=[39, 41], penalty=0)
    assert dsq(course=['31', '41(41,42)'], splits=[31, 49], penalty=0)


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
    ResultChecker.calculate_penalty(result)
    result_penalty = get_penalty(result)
    return result.status == result_status, result_penalty == penalty


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


def get_penalty(result: ResultSportident) -> int:
    marked_route_mode = race().get_setting('marked_route_mode', 'off')
    if marked_route_mode == 'laps':
        return result.penalty_laps
    elif marked_route_mode == 'time':
        penalty_time = race().get_setting('marked_route_penalty_time', 60000)
        return result.penalty_time.to_msec() / penalty_time
    else:
        return 0
