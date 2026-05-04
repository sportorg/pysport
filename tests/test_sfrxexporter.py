import importlib
import os
import shutil
import sys
import tempfile
import types
from datetime import date, datetime
from enum import Enum, IntEnum
from unittest.mock import Mock, patch

import pytest

from sportorg.common.otime import OTime


class RaceType(Enum):
    INDIVIDUAL_RACE = 0
    RELAY = 3


class ResultStatus(Enum):
    OK = 1
    DISQUALIFIED = 3
    OVERTIME = 8
    DID_NOT_START = 13
    RESTORED = 16


class Qualification(IntEnum):
    NOT_QUALIFIED = 0


@pytest.fixture()
def sfrxexporter(monkeypatch):
    fake_memory = types.ModuleType("sportorg.models.memory")
    fake_memory.Qualification = Qualification
    fake_memory.Race = object
    fake_memory.RaceType = RaceType
    fake_memory.ResultStatus = ResultStatus
    fake_memory.race = Mock()

    import sportorg.models

    monkeypatch.setattr(sportorg.models, "memory", fake_memory, raising=False)
    monkeypatch.setitem(sys.modules, "sportorg.models.memory", fake_memory)
    sys.modules.pop("sportorg.modules.sfr.sfrxexporter", None)

    module = importlib.import_module("sportorg.modules.sfr.sfrxexporter")
    yield module

    sys.modules.pop("sportorg.modules.sfr.sfrxexporter", None)


class TestSFRxExporter:
    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_export.sfrx")
        self.create_mock_race()

    def teardown_method(self):
        shutil.rmtree(self.test_dir)

    def create_mock_race(self, race_type=RaceType.INDIVIDUAL_RACE, **kwargs):
        self.race = types.SimpleNamespace()
        self.race.data = types.SimpleNamespace()
        self.race.data.title = kwargs.get("title", "Тестовые соревнования")
        self.race.data.location = kwargs.get("location", "Тестовая локация")
        self.race.data.start_datetime = kwargs.get(
            "start_datetime", datetime(2024, 1, 15, 10, 0, 0)
        )
        self.race.data.race_type = race_type
        self.race.data.description = kwargs.get("description", "Тестовое описание")
        self.race.data.chief_referee = kwargs.get("chief_referee", "Главный судья")
        self.race.data.secretary = kwargs.get("secretary", "Секретарь")

        self.group1 = self.create_mock_group(
            name="М21",
            course=self.create_mock_course(
                name="Длинная",
                controls=[
                    self.create_mock_control("31"),
                    self.create_mock_control("32"),
                ],
            ),
        )
        self.org1 = self.create_mock_organization("СК Приз")
        self.person1 = self.create_mock_person(
            name="Иван",
            surname="Иванов",
            bib=101,
            group=self.group1,
            organization=self.org1,
            birth_date=date(1990, 5, 15),
            start_time=OTime(hour=10, minute=30),
        )
        self.result1 = self.create_mock_result(
            person=self.person1,
            start_time=OTime(hour=10, minute=30),
            finish_time=OTime(hour=11, minute=15, sec=30),
            status=ResultStatus.OK,
            splits=[
                self.create_mock_split("31", OTime(hour=10, minute=45)),
                self.create_mock_split("32", OTime(hour=11)),
            ],
        )

        self.race.groups = [self.group1]
        self.race.organizations = [self.org1]
        self.race.persons = [self.person1]
        self.race.courses = [self.group1.course]
        self.race.results = [self.result1]
        self.race.relay_teams = []
        self.race.settings = {"live_urls": ["http://test.org/geo"]}
        self.race.controls = []
        self.race.find_person_result = Mock(return_value=self.result1)
        self.race.get_setting = lambda key, default=None: self.race.settings.get(
            key, default
        )

    def create_mock_group(self, name, course=None):
        return types.SimpleNamespace(name=name, course=course)

    def create_mock_course(self, name, controls=None, **kwargs):
        return types.SimpleNamespace(
            name=name,
            bib=kwargs.get("bib", 1),
            length=kwargs.get("length", 4200),
            climb=kwargs.get("climb", 150),
            controls=controls or [],
        )

    def create_mock_control(self, code):
        return types.SimpleNamespace(
            code=code,
            length=0,
            get_number_code=Mock(return_value=code),
        )

    def create_mock_organization(self, name):
        return types.SimpleNamespace(name=name)

    def create_mock_person(self, name, surname, bib, group, organization, **kwargs):
        return types.SimpleNamespace(
            name=name,
            surname=surname,
            middle_name=kwargs.get("middle_name", ""),
            bib=bib,
            group=group,
            organization=organization,
            birth_date=kwargs.get("birth_date"),
            year=kwargs.get("year", 1990),
            qual=kwargs.get("qual", Qualification.NOT_QUALIFIED),
            comment=kwargs.get("comment", ""),
            start_time=kwargs.get("start_time"),
            is_out_of_competition=kwargs.get("is_out_of_competition", False),
        )

    def create_mock_result(self, person, start_time, finish_time, status, splits=None):
        return types.SimpleNamespace(
            person=person,
            start_time=start_time,
            finish_time=finish_time,
            status=status,
            splits=splits or [],
            get_start_time=Mock(return_value=start_time),
            get_finish_time=Mock(return_value=finish_time),
            get_result_otime=Mock(
                return_value=finish_time - start_time
                if status == ResultStatus.OK and start_time and finish_time
                else OTime()
            ),
        )

    def create_mock_split(self, code, time):
        return types.SimpleNamespace(code=code, time=time, is_correct=True)

    def read_rows(self):
        with open(self.test_file, encoding="utf-8") as f:
            return [line.rstrip("\n").split("\t") for line in f]

    def test_export_sfrx_success(self, sfrxexporter):
        sfrxexporter.memory.race.return_value = self.race
        sfrxexporter.translate = lambda x: x

        result = sfrxexporter.export_sfrx(self.test_file)

        assert result is True
        assert os.path.exists(self.test_file)

        rows = self.read_rows()
        competitor = next(row for row in rows if row[0].startswith("c"))
        split = next(row for row in rows if row[0].startswith("s"))

        assert competitor[13] == "10:30:00"
        assert competitor[14] == "11:15:30"
        assert competitor[16] == "00:45:30"
        assert split[6:] == [
            "31",
            "1",
            "10:45:00",
            "32",
            "2",
            "11:00:00",
            "240",
            "0",
            "11:15:30",
        ]

    def test_export_sfrx_no_race_data(self, sfrxexporter):
        sfrxexporter.memory.race.return_value = None
        sfrxexporter.translate = lambda x: x

        with patch.object(sfrxexporter.logging, "error") as mock_logging_error:
            result = sfrxexporter.export_sfrx(self.test_file)

        assert result is False
        mock_logging_error.assert_called_with("No race data found")

    def test_export_sfrx_with_relay(self, sfrxexporter):
        self.create_mock_race(RaceType.RELAY)
        sfrxexporter.memory.race.return_value = self.race
        sfrxexporter.translate = lambda x: x

        result = sfrxexporter.export_sfrx(self.test_file)

        assert result is True
        assert self.read_rows()[0][7] == "Эстафета"

    def test_export_sfrx_different_result_statuses(self, sfrxexporter):
        person_dsq = self.create_mock_person(
            name="Петр",
            surname="Петров",
            bib=102,
            group=self.group1,
            organization=self.org1,
            birth_date=date(1995, 3, 20),
            start_time=OTime(hour=10, minute=35),
        )
        result_dsq = self.create_mock_result(
            person=person_dsq,
            start_time=OTime(hour=10, minute=35),
            finish_time=OTime(hour=11, minute=20),
            status=ResultStatus.DISQUALIFIED,
        )

        self.race.persons = [self.person1, person_dsq]
        self.race.results = [self.result1, result_dsq]

        def find_result_side_effect(person):
            if person.bib == 101:
                return self.result1
            if person.bib == 102:
                return result_dsq
            return None

        self.race.find_person_result.side_effect = find_result_side_effect
        sfrxexporter.memory.race.return_value = self.race
        sfrxexporter.translate = lambda x: x

        result = sfrxexporter.export_sfrx(self.test_file)

        assert result is True
        rows = self.read_rows()
        dsq_competitor = next(row for row in rows if row[1] == "102")

        assert dsq_competitor[3] == "Петров"
        assert dsq_competitor[16] == "cнят"

    def test_export_sfrx_exception_handling(self, sfrxexporter):
        sfrxexporter.memory.race.return_value = self.race
        sfrxexporter.translate = lambda x: x

        with patch("builtins.open", side_effect=Exception("Test error")):
            result = sfrxexporter.export_sfrx(self.test_file)

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
