from sportorg.libs.sfr import sfrximporter
from sportorg.models.memory import (
    Group,
    Organization,
    Person,
    Qualification,
    find,
    ResultStatus,
    races,
)
from sportorg.utils.time import hhmmss_to_time


def test_import_sfrx():
    sfrximporter.import_sfrx("tests/data/sfrx_file.sfrx")
    assert len(races()) == 2, "Count races error"

    test_cases = [
        {
            "person": {"name": "Имя1", "surname": "Фамилия1", "bib": 101},
            "expected": {
                "middle_name": "Отчество1",
                "group_name": "Группа1",
                "org_name": "Команда1",
                "year": 2001,
                "birthday": "05.05.2001",
                "card_number": 0,
                "qual": Qualification.I,
                "day_data": [
                    {  # Day 0
                        "course_name": "Дист1",
                        "start": "12:01:00",
                        "finish": "13:01:00",
                        "status": ResultStatus.OK,
                        "split_code": "31",
                    },
                    {  # Day 1
                        "course_name": "Финал",
                        "start": "15:01:00",
                        "finish": "17:01:00",
                        "status": ResultStatus.OK,
                        "split_code": "41",
                    },
                ],
            },
        },
        {
            "person": {"name": "Имя2", "surname": "Фамилия2", "bib": 201},
            "expected": {
                "middle_name": "Отчество2",
                "group_name": "Группа2",
                "org_name": "Команда2",
                "year": 2002,
                "birthday": "01.01.2002",
                "card_number": 0,
                "qual": Qualification.II,
                "day_data": [
                    {  # Day 0
                        "course_name": "Дист2",
                        "start": "12:02:00",
                        "finish": "14:02:00",
                        "status": ResultStatus.OK,
                        "split_code": "52",
                    },
                    {  # Day 1
                        "course_name": "Полуфинал",
                        "start": "15:04:00",
                        "finish": "15:06:00",
                        "status": ResultStatus.DISQUALIFIED,
                        "split_code": "51",
                    },
                ],
            },
        },
    ]

    for test_case in test_cases:
        _test_person_data(test_case)


def _test_person_data(test_case):
    person_data = test_case["person"]
    expected = test_case["expected"]

    for day in range(2):
        cur_race = races()[day]
        person = find(cur_race.persons, **person_data)

        assert person.middle_name == expected["middle_name"], "Middle name error"
        assert person.bib == person_data["bib"], "Bib error"
        assert isinstance(person, Person), "Not person"
        assert isinstance(person.group, Group), "Not group"
        assert person.group.name == expected["group_name"], "Group name error"
        assert isinstance(person.organization, Organization), "Not organization"
        assert person.organization.name == expected["org_name"], (
            "Organization name error"
        )
        assert person.get_year() == expected["year"], "Year error"
        assert person.get_birthday() == expected["birthday"], "Birthday error"
        assert person.card_number == expected["card_number"], "Card number error"
        assert person.qual == expected["qual"], "Qualification error"

        # Проверка результатов для текущего дня
        day_expected = expected["day_data"][day]
        result = find(cur_race.results, bib=person_data["bib"])

        assert person.group.course.name == day_expected["course_name"], (
            "Course name error"
        )
        assert result.start_time == hhmmss_to_time(day_expected["start"]), "Start error"
        assert result.finish_time == hhmmss_to_time(day_expected["finish"]), (
            "Finish error"
        )
        assert result.status == day_expected["status"], "Result status error"
        assert len(result.splits) > 0, "Split len error"
        assert result.splits[0].code == day_expected["split_code"], "Split code error"
