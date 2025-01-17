import logging
from typing import List, Tuple

from sportorg.common.otime import OTime
from sportorg.models.memory import (
    Course,
    Group,
    Person,
    Race,
    ResultSportident,
    Split,
    create,
    new_event,
    race,
    ResultStatus,
)
from sportorg.models.result.result_checker import ResultChecker
from sportorg.utils.time import hhmmss_to_time


# Настройки подсчета отсечки.
# credit_time_enabled [bool] - включен подсчет отсечки или нет
# credit_time_сp [int] - номер контрольного пункта отсечки


def test_credit_calculation():
    create_race()

    race().set_setting("credit_time_enabled", False)
    race().set_setting("credit_time_cp", 41)

    assert ok(
        splits=[
            ("31", "01:00:00"),
            ["41", "01:02:35"],
            ["51", "02:03:35"],
            ["41", "03:01:35"],
        ],
        expected_result=OTime(),
    )
    assert ok(
        splits=[
            ("31", "12:03:00"),
            ["41", "13:04:35"],
            ["51", "14:02:35"],
            ["41", "15:02:35"],
        ],
        expected_result=OTime(),
    )

    race().set_setting("credit_time_enabled", True)

    assert ok(
        splits=[
            ("31", "01:00:00"),
            ["41", "01:02:35"],
            ["51", "02:03:35"],
            ["41", "03:01:35"],
        ],
        expected_result=hhmmss_to_time("01:00:35"),
    )
    assert ok(
        splits=[
            ("31", "12:03:00"),
            ["41", "13:04:35"],
            ["51", "14:02:35"],
            ["41", "15:02:35"],
        ],
        expected_result=hhmmss_to_time("02:01:35"),
    )


def ok(splits: List[Tuple], expected_result: OTime) -> bool:
    """Проверка отсечки

    Parameters
    ----------
    splits : List[(int, str)]
        Отметки спортсмена на дистанции
    expected_result : OTime
        ожидаемый результат отсечки

    Returns
    -------
    bool
        Возвращает True если отсечка совпадает
    """

    result = race().results[0]
    result.splits = make_splits(splits)

    result.status = ResultStatus.OK
    ResultChecker.checking(result)
    result_credit = result.get_credit_time()
    check_result = result_credit == expected_result

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


def make_splits(splits: List[Tuple]) -> List[Split]:
    return [
        create(Split, code=str(code), time=hhmmss_to_time(time))
        for code, time in splits
    ]
