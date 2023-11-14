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

# Настройки проверки отметки, относящиеся к маркированной трассе.
# marked_route_mode [str] - режим начисления штрафа. Допустимые значения:
#   'off' - штраф не начисляется
#   'time' - начисляется штрафное время
#   'laps' - начисляются штрафные круги
#       default value: marked_route_mode = 'off'
# marked_route_penalty_time [int] - стоимость одного штрафа в миллисекундах (ms)
#       default value: marked_route_penalty_time = 60000
# marked_route_if_counting_lap [bool] - режим проверки количества пройденных штрафных кругов
#       default value: marked_route_if_counting_lap = True
# marked_route_if_station_check [bool] - режим проверки количества пройденных штрафных кругов
#       default value: marked_route_if_station_check = False
# marked_route_station_code [int] - номер станции на штрафном круге
#       default value: marked_route_station_code = 80
# marked_route_dont_dsq [bool] - дисквалифицировать ли спортсмена за пропущенные КП
#   True - проверяет функцией penalty_calculation_free_order()
#   False - проверяет функцией penalty_calculation(<...>, check_existence=True)
#       default value: marked_route_dont_dsq = False
# marked_route_max_penalty_by_cp [bool] - максимальный штраф - количество КП на дистанции
#       default value: marked_route_max_penalty_by_cp = False


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


def test_marked_route_yes_no():
    """Тест маркированной трассы по варианту ДА/НЕТ.

    На дистанции устанавливаются контрольные пункты. На карте нарисованы
    контрольные пункты. Спортсмен движется, встречая контрольный пункт
    на местности, должен определить: нанесён контрольный пункт на карту или нет.
    Если данный контрольный пункт есть в карте, спортсмену следует отметиться
    в станции ДА. Если контрольного пункта нет в карте, спортсмену следует
    отметиться в станции НЕТ. За неправильную отметку спортсмен получает штраф.
    За отсутствующую отметку спортсмен должен быть дисквалифицирован.
    """
    # fmt: off
    create_race()
    race().set_setting('marked_route_mode', 'time')

    # Отметка ок, без штрафа
    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31,          41,          51,         100], penalty=0)

    # Отметка ок, 1 штраф - неверный выбор на одном КП
    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31,          42,          51,         100], penalty=1)

    # Отметка ок, 3 штрафа - неверный выбор на трёх КП
    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 32,          42,          52,         100], penalty=3)

    # Отметка ок, 0 штрафа - лишняя отметка на одном истинном КП
    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31, 31,      41,          51,         100], penalty=0)

    # Отметка ок, 1 штраф - лишняя отметка на одном ложном КП
    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31,          41,          52, 52,     100], penalty=1)

    # Отметка ок, 1 штраф - отметка на обоих станциях на одном КП
    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 32, 31,      41,          51,         100], penalty=1)

    # Дисквалифицирован, 1 штраф - отсутствует отметка на одном КП
    assert dsq(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31,                       51,         100], penalty=1)

    # Дисквалифицирован, 1 штраф - отсутствует отметка на последнем КП100
    assert dsq(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31,          41,          51,            ], penalty=1)

    # Дисквалифицирован, 4 штрафа - пустой чип
    assert dsq(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[                                          ], penalty=4)

    # Отметка ок, 0 штрафа - отметка на КП, которого нет на карте
    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31, 75,      41,          51,         100], penalty=0)

    # Отметка ок, 0 штрафа - отметка на КП, которого нет на карте
    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 31, 75,      41,          51,         100], penalty=0)

    # Отметка ок, 0 штрафа - неочищенный чип НЕ содержит часть дистанции
    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 70, 71, 72, 73,   31, 41, 51,         100], penalty=0)

    # Отметка ок, 1 штраф - неочищенный чип содержит часть дистанции
    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 40, 41, 42, 43,   31, 41, 51,         100], penalty=1)
    assert  ok(course=['31(31,32)', '41(41,42)', '51(51,52)', 100],
               splits=[ 40, 41, 42, 43,   31, 42, 51,         100], penalty=1)
    # fmt: on


def test_penalty_calculation_function():
    """Тесты из строки документации к функции penalty_calculation()

    В этом тесте вызывается penalty_calculation(<...>, check_existence=True)
    так как с параметрами penalty_calculation(<...>, check_existence=False)
    эта функция нигде не вызывается.
    """
    # fmt: off
    create_race()
    race().set_setting('marked_route_mode', 'time')

    # return quantity of incorrect or duplicated punches, order is ignored
    # origin: 31,41,51; athlete: 31,41,51; result:0
    assert  ok(course=[31, 41, 51],
               splits=[31, 41, 51], penalty=0)

    # origin: 31,41,51; athlete: 31; result:0
    # check_existence=False
    assert 0 == ResultChecker.penalty_calculation(
        splits=make_splits([31]),
        controls=make_course_controls([31, 41, 51]), check_existence=False)

    # origin: 31,41,51; athlete: 31; result:2
    # check_existence=True
    assert dsq(course=[31, 41, 51],
               splits=[31,       ], penalty=2)

    # origin: 31,41,51; athlete: 41,31,51; result:0
    assert dsq(course=[31, 41, 51],
               splits=[41, 31, 51], penalty=0)

    # origin: 31,41,51; athlete: 41,31,51; result:0
    assert dsq(course=[31, 41, 51],
               splits=[41, 31, 51], penalty=0)

    # origin: 31,41,51; athlete: 31,42,51; result:1
    assert dsq(course=[31, 41, 51],
               splits=[31, 42, 51], penalty=1)

    # origin: 31,41,51; athlete: 31,41,51,52; result:1
    assert  ok(course=[31, 41, 51],
               splits=[31, 41, 51, 52], penalty=1)

    # origin: 31,41,51; athlete: 31,42,51,52; result:2
    assert dsq(course=[31, 41, 51],
               splits=[31, 42, 51, 52], penalty=2)

    # origin: 31,41,51; athlete: 31,31,41,51; result:1
    assert  ok(course=[31, 41, 51],
               splits=[31, 31, 41, 51], penalty=1)

    # origin: 31,41,51; athlete: 31,41,51,51; result:1
    assert  ok(course=[31, 41, 51],
               splits=[31, 41, 51, 51], penalty=1)

    # origin: 31,41,51; athlete: 32,42,52; result:3
    assert dsq(course=[31, 41, 51],
               splits=[32, 42, 52], penalty=3)

    # origin: 31,41,51; athlete: 31,41,51,61,71,81,91; result:4
    assert  ok(course=[31, 41, 51],
               splits=[31, 41, 51, 61, 71, 81, 91], penalty=4)

    # origin: 31,41,51; athlete: 31,41,52,61,71,81,91; result:5
    assert dsq(course=[31, 41, 51],
               splits=[31, 41, 52, 61, 71, 81, 91], penalty=5)

    # origin: 31,41,51; athlete: 51,61,71,81,91,31,41; result:4
    assert dsq(course=[31, 41, 51],
               splits=[51, 61, 71, 81, 91, 31, 41], penalty=4)

    # origin: 31,41,51; athlete: 51,61,71,81,91,32,41; result:5
    assert dsq(course=[31, 41, 51],
               splits=[51, 61, 71, 81, 91, 32, 41], penalty=5)

    # origin: 31,41,51; athlete: 51,61,71,81,91,32,42; result:6
    assert dsq(course=[31, 41, 51],
               splits=[51, 61, 71, 81, 91, 32, 42], penalty=6)

    # origin: 31,41,51; athlete: 52,61,71,81,91,32,42; result:7
    assert dsq(course=[31, 41, 51],
               splits=[52, 61, 71, 81, 91, 32, 42], penalty=7)

    # origin: 31,41,51; athlete: no punches; result:0
    # check_existence=False
    assert 0 == ResultChecker.penalty_calculation(
        splits=make_splits([]),
        controls=make_course_controls([31, 41, 51]), check_existence=False)

    # origin: 31,41,51; athlete: no punches; result:3
    # check_existence=True
    assert dsq(course=[31, 41, 51],
               splits=[], penalty=3)

    # wildcard support for free order
    # origin: *,*,* athlete: 31; result:2
    # check_existence=False
    assert 0 == ResultChecker.penalty_calculation(
        splits=make_splits([31]),
        controls=make_course_controls(['*', '*', '*']), check_existence=False)

    # check_existence=True
    assert dsq(course=['*', '*', '*'],
               splits=[31], penalty=2)

    # origin: *,*,* athlete: 31,31; result:2 //wrong
    # check_existence=False
    assert 0 == ResultChecker.penalty_calculation(
        splits=make_splits([31, 31]),
        controls=make_course_controls(['*', '*', '*']), check_existence=False)

    # check_existence=True
    assert dsq(course=['*', '*', '*'],
               splits=[31, 31], penalty=1)

    # origin: *,*,* athlete: 31,31,31,31; result:3 //wrong
    # check_existence=False
    assert 1 == ResultChecker.penalty_calculation(
        splits=make_splits([31, 31, 31, 31]),
        controls=make_course_controls(['*', '*', '*']), check_existence=False)

    # check_existence=True
    assert dsq(course=['*', '*', '*'],
               splits=[31, 31, 31, 31], penalty=1)
    # fmt: on


def test_non_obvious_behavior():
    """Неочевидное поведение при проверке дистанции. Не всегда это некорректная работа
    алгоритма, иногда может возникать из-за недочётов при составлении курсов.
    """
    create_race()
    race().set_setting('marked_route_mode', 'laps')

    # Различие в обработке двух случаев. Тестовый случай:
    # 1) Спортсмен пропустил нужный КП -> получает штраф
    # 2) Спортсмен пропустил нужный КП, но отметился на чужом -> нет штрафа
    # Должен быть одинаковый штраф. Или начисляться за каждый лишний КП.
    # Но лишние отметки в чипе не должны уменьшать количество штрафа.
    # Да, по результатам проверки спортсмен снят. Но его могут восстановить
    # решением судьи, а штрафные круги он уже пробежал.
    assert dsq(course=['31', '41(41,42)'], splits=[31], penalty=1)
    assert dsq(course=['31', '41(41,42)'], splits=[41], penalty=1)
    assert dsq(course=['31', '41(41,42)'], splits=[39, 41], penalty=0)
    assert dsq(course=['31', '41(41,42)'], splits=[31, 49], penalty=0)

    # Различные способы задания дистанции приводят к различному
    # начислению штрафа за лишние отметки
    assert ok(course=['31', '41'], splits=[31, 77, 41], penalty=1)
    assert ok(course=['31', '41(41,42)'], splits=[31, 77, 41], penalty=0)


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
    заранее и хранятся в объекте race().get_settings().

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


def exception_message(
    course: List[Union[int, str]],
    splits: List[int],
    result_status_expected: ResultStatus,
    result_status_received: ResultStatus,
    penalty_expected: int,
    penalty_received: int,
) -> str:
    """Формирование отладочного сообщения при создании исключения. Отладочное
    сообщение содержит сравнение дистанции и отметок и причину несоответствия.

    Parameters
    ----------
    course : List[Union[int, str]]
        Порядок прохождения дистанции
    splits : List[int]
        Отметки спортсмена на дистанции
    result_status_expected : ResultStatus,
        Ожидаемый результат проверки.
    result_status_received : ResultStatus,
        Полученный результат проверки.
    penalty_expected : int
        Ожидаемое количество штрафа.
    penalty_received : int
        Полученное количество штрафа.

    Returns
    -------
    str
        Строка отладочного сообщения
    """
    message = 'Check failed'
    message += '\n' + split_and_course_repr(course, splits)
    if result_status_expected != result_status_received:
        message += '\n' + f'Result status failed!'
        message += '\n' + f'Expected: {result_status_expected}'
        message += '\n' + f'Received: {result_status_received}'
    if penalty_expected != penalty_received:
        message += '\n' + f'Penalty failed!'
        message += '\n' + f'Expected: {penalty_expected}'
        message += '\n' + f'Received: {penalty_received}'
    return message


def split_and_course_repr(course: List[Union[int, str]], splits: List[int]) -> str:
    """Формирование строки для визуального сравнения отметок и дистанции.
    Spl  Crs
     31  31
     41  41
     52  51(51,52)

    Parameters
    ----------
    course : List[Union[int, str]]
        Порядок прохождения дистанции
    splits : List[int]
        Отметки спортсмена на дистанции

    Returns
    -------
    str
        Строка со сравнением отметок и дистанции
    """
    spl = ['Spl'] + splits
    crs = ['Crs'] + course
    return '\n'.join([f'{s:3}  {c}' for s, c in zip_longest(spl, crs, fillvalue='')])
