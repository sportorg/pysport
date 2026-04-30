import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import pytest

from sportorg.models.memory import (
    RaceType, ResultStatus, Qualification, OTime,
    Race, RaceData, Person, Group, Organization, 
    Course, CourseControl, Split, ResultSportident
)


class TestSFRxExporter:
    """Упрощенные тесты для экспорта SFRx"""
    
    def setup_method(self):
        """Базовая настройка для всех тестов"""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_export.sfrx")
        
        # Создаем мок-объекты
        self.create_mock_race()
    
    def teardown_method(self):
        """Очистка после тестов"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.test_dir)
    
    def create_mock_race(self, race_type=RaceType.INDIVIDUAL_RACE, **kwargs):
        """Создание мок-объекта гонки с параметрами"""
        self.race = Mock(spec=Race)
        self.race.data = Mock(spec=RaceData)
        self.race.data.title = kwargs.get('title', "Тестовые соревнования")
        self.race.data.location = kwargs.get('location', "Тестовая локация")
        self.race.data.start_datetime = kwargs.get('start_datetime', datetime(2024, 1, 15, 10, 0, 0))
        self.race.data.race_type = race_type
        self.race.data.description = kwargs.get('description', "Тестовое описание")
        self.race.data.chief_referee = kwargs.get('chief_referee', "Главный судья")
        self.race.data.secretary = kwargs.get('secretary', "Секретарь")
        
        # Базовая группа
        self.group1 = self.create_mock_group(
            name="М21",
            course=self.create_mock_course(
                name="Длинная",
                controls=[
                    self.create_mock_control("31"),
                    self.create_mock_control("32")
                ]
            )
        )
        
        # Базовая организация
        self.org1 = self.create_mock_organization("СК Приз")
        
        # Базовый участник
        self.person1 = self.create_mock_person(
            name="Иван",
            surname="Иванов",
            bib=101,
            group=self.group1,
            organization=self.org1,
            birth_date=date(1990, 5, 15),
            start_time=OTime(10, 30, 0)
        )
        
        # Базовый результат
        self.result1 = self.create_mock_result(
            person=self.person1,
            start_time=OTime(10, 30, 0),
            finish_time=OTime(11, 15, 30),
            status=ResultStatus.OK,
            splits=[
                self.create_mock_split("31", OTime(10, 45, 0)),
                self.create_mock_split("32", OTime(11, 0, 0))
            ]
        )
        
        # Настройка гонки
        self.race.groups = [self.group1]
        self.race.organizations = [self.org1]
        self.race.persons = [self.person1]
        self.race.courses = [self.group1.course]
        self.race.results = [self.result1]
        self.race.relay_teams = []
        self.race.settings = {'live_urls': ['http://test.org/geo']}
        self.race.controls = []
        
        self.race.find_person_result = Mock(return_value=self.result1)
        self.race.get_setting = lambda key, default=None: self.race.settings.get(key, default)
    
    def create_mock_group(self, name, course=None):
        group = Mock(spec=Group)
        group.name = name
        group.course = course
        return group
    
    def create_mock_course(self, name, controls=None, **kwargs):
        course = Mock(spec=Course)
        course.name = name
        course.bib = kwargs.get('bib', 1)
        course.length = kwargs.get('length', 4200)
        course.climb = kwargs.get('climb', 150)
        course.controls = controls or []
        return course
    
    def create_mock_control(self, code):
        control = Mock(spec=CourseControl)
        control.code = code
        control.length = 0
        control.get_number_code = Mock(return_value=code)
        return control
    
    def create_mock_organization(self, name):
        org = Mock(spec=Organization)
        org.name = name
        return org
    
    def create_mock_person(self, name, surname, bib, group, organization, **kwargs):
        person = Mock(spec=Person)
        person.name = name
        person.surname = surname
        person.middle_name = kwargs.get('middle_name', '')
        person.bib = bib
        person.group = group
        person.organization = organization
        person.birth_date = kwargs.get('birth_date')
        person.year = kwargs.get('year', 1990)
        person.qual = kwargs.get('qual', Qualification.NOT_QUALIFIED)
        person.comment = kwargs.get('comment', "")
        person.start_time = kwargs.get('start_time')
        person.is_out_of_competition = kwargs.get('is_out_of_competition', False)
        return person
    
    def create_mock_result(self, person, start_time, finish_time, status, splits=None):
        result = Mock(spec=ResultSportident)
        result.person = person
        result.start_time = start_time
        result.finish_time = finish_time
        result.status = status
        result.splits = splits or []
        result.get_start_time = Mock(return_value=start_time)
        result.get_finish_time = Mock(return_value=finish_time)
        return result
    
    def create_mock_split(self, code, time):
        split = Mock(spec=Split)
        split.code = code
        split.time = time
        split.is_correct = True
        return split
    
    @patch('sportorg.modules.sfr.sfrxexporter.memory')
    @patch('sportorg.modules.sfr.sfrxexporter.logging')
    @patch('sportorg.modules.sfr.sfrxexporter.translate')
    def test_export_sfrx_success(self, mock_translate, mock_logging, mock_memory):
        """Базовый успешный экспорт"""
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
        
        from sportorg.modules.sfr.sfrxexporter import export_sfrx
        result = export_sfrx(self.test_file)
        
        assert result is True
        assert os.path.exists(self.test_file)
        mock_logging.info.assert_called()
    
    @patch('sportorg.modules.sfr.sfrxexporter.memory')
    @patch('sportorg.modules.sfr.sfrxexporter.logging')
    @patch('sportorg.modules.sfr.sfrxexporter.translate')
    def test_export_sfrx_no_race_data(self, mock_translate, mock_logging, mock_memory):
        """Экспорт без данных гонки"""
        mock_memory.race.return_value = None
        mock_translate.side_effect = lambda x: x
        
        from sportorg.modules.sfr.sfrxexporter import export_sfrx
        result = export_sfrx(self.test_file)
        
        assert result is False
        mock_logging.error.assert_called_with("No race data found")
    
    @patch('sportorg.modules.sfr.sfrxexporter.memory')
    @patch('sportorg.modules.sfr.sfrxexporter.logging')
    @patch('sportorg.modules.sfr.sfrxexporter.translate')
    def test_export_sfrx_with_relay(self, mock_translate, mock_logging, mock_memory):
        """Экспорт эстафеты"""
        self.create_mock_race(RaceType.RELAY)
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
        
        from sportorg.modules.sfr.sfrxexporter import export_sfrx
        result = export_sfrx(self.test_file)
        
        assert result is True
        assert os.path.exists(self.test_file)
    
    @patch('sportorg.modules.sfr.sfrxexporter.memory')
    @patch('sportorg.modules.sfr.sfrxexporter.logging')
    @patch('sportorg.modules.sfr.sfrxexporter.translate')
    def test_export_sfrx_different_result_statuses(self, mock_translate, mock_logging, mock_memory):
        """Экспорт с разными статусами результатов"""
        # Создаем участников с разными статусами
        person_dsq = self.create_mock_person(
            name="Петр", surname="Петров", bib=102,
            group=self.group1, organization=self.org1,
            birth_date=date(1995, 3, 20)
        )
        
        result_dsq = self.create_mock_result(
            person=person_dsq,
            start_time=OTime(10, 35, 0),
            finish_time=OTime(11, 20, 0),
            status=ResultStatus.DISQUALIFIED
        )
        
        # Обновляем гонку
        self.race.persons = [self.person1, person_dsq]
        self.race.results = [self.result1, result_dsq]
        
        def find_result_side_effect(person):
            if person.bib == 101:
                return self.result1
            elif person.bib == 102:
                return result_dsq
            return None
        
        self.race.find_person_result.side_effect = find_result_side_effect
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
        
        from sportorg.modules.sfr.sfrxexporter import export_sfrx
        result = export_sfrx(self.test_file)
        
        assert result is True
        
        with open(self.test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Иванов" in content
            assert "Петров" in content
    
    @patch('sportorg.modules.sfr.sfrxexporter.memory')
    @patch('sportorg.modules.sfr.sfrxexporter.logging')
    @patch('sportorg.modules.sfr.sfrxexporter.translate')
    def test_export_sfrx_exception_handling(self, mock_translate, mock_logging, mock_memory):
        """Обработка исключений при экспорте"""
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
        
        from sportorg.modules.sfr.sfrxexporter import export_sfrx
        
        # Симулируем ошибку при открытии файла
        with patch('builtins.open', side_effect=Exception("Test error")):
            result = export_sfrx(self.test_file)
            
            assert result is False
            mock_logging.error.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])