# test_sfrxexporter.py
# import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from uuid import uuid4

from sportorg.models.memory import (
    RaceType, ResultStatus, Qualification, OTime,
    Race, RaceData, Person, Group, Organization, 
    Course, CourseControl, Split, ResultSportident
)


class TestSFRxExporter:
      def setup_method(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_export.sfrx")
        self.race = Mock(spec=Race)
        self.race.data = Mock(spec=RaceData)
        self.race.data.title = "Тестовые соревнования"
        self.race.data.location = "Тестовая локация"
        self.race.data.start_datetime = datetime(2024, 1, 15, 10, 0, 0)
        self.race.data.race_type = RaceType.INDIVIDUAL_RACE
        
        self.group1 = Mock(spec=Group)
        self.group1.name = "М21"
        self.group1.course = None
        self.group1.get_type = Mock(return_value=RaceType.INDIVIDUAL_RACE)
        self.group1.is_relay = Mock(return_value=False)
       
        self.course1 = Mock(spec=Course)
        self.course1.name = "Длинная"
        self.course1.bib = 1
        self.course1.length = 4200
        self.course1.climb = 150
        
        self.control1 = Mock(spec=CourseControl)
        self.control1.code = "31"
        self.control1.length = 0
        self.control1.get_number_code = Mock(return_value="31")
        
        self.control2 = Mock(spec=CourseControl)
        self.control2.code = "32"
        self.control2.length = 0
        self.control2.get_number_code = Mock(return_value="32")
        
        self.course1.controls = [self.control1, self.control2]
        self.group1.course = self.course1
        
        self.org1 = Mock(spec=Organization)
        self.org1.name = "СК Приз"
        
        self.person1 = Mock(spec=Person)
        self.person1.id = uuid4()
        self.person1.name = "Иван"
        self.person1.surname = "Иванов"
        self.person1.middle_name = "Иванович"
        self.person1.bib = 101
        self.person1.group = self.group1
        self.person1.organization = self.org1
       
        self.person1.birth_date = date(1990, 5, 15)
        
        self.person1.year = 1990
        
        self.person1.qual = Qualification.NOT_QUALIFIED
        
        self.person1.comment = "Тестовый участник"
        
        self.person1.start_time = OTime(10, 30, 0)
    
        self.person1.is_out_of_competition = False
        self.person1.is_rented_card = False
        self.person1.is_paid = False
        self.person1.is_personal = False
        self.person1.world_code = ""
        self.person1.national_code = 0
        self.person1.card_number = 123456
        self.person1.start_group = 0
        self.person1.result_count = 0
      
        self.person1.full_name = "Иванов Иван"
        
        self.result1 = Mock(spec=ResultSportident)
        self.result1.id = uuid4()
        self.result1.person = self.person1
      
        self.result1.start_time = OTime(10, 30, 0)
        self.result1.finish_time = OTime(11, 15, 30)
        self.result1.status = ResultStatus.OK
        self.result1.status_comment = ""
        self.result1.penalty_time = None
        self.result1.credit_time = None
        self.result1.penalty_laps = 0
        self.result1.place = 0
        self.result1.scores = 0
        self.result1.rogaine_score = 0
        self.result1.scores_ardf = 0
        self.result1.card_number = 123456
       
        self.split1 = Mock(spec=Split)
        self.split1.code = "31"
        self.split1.time = OTime(10, 45, 0)
        self.split1.is_correct = True
        
        self.split2 = Mock(spec=Split)
        self.split2.code = "32"
        self.split2.time = OTime(11, 0, 0)
        self.split2.is_correct = True
        
        self.result1.splits = [self.split1, self.split2]
      
        self.result1.get_start_time = Mock(return_value=OTime(10, 30, 0))
        self.result1.get_finish_time = Mock(return_value=OTime(11, 15, 30))
        self.result1.get_penalty_time = Mock(return_value=OTime())
        self.result1.get_credit_time = Mock(return_value=OTime())
        self.result1.is_status_ok = Mock(return_value=True)
        self.result1.is_sportident = Mock(return_value=True)
        
        self.race.groups = [self.group1]
        self.race.organizations = [self.org1]
        self.race.persons = [self.person1]
        self.race.courses = [self.course1]
        self.race.results = [self.result1]
        self.race.relay_teams = []
        self.race.settings = {}
        self.race.controls = []
        
        self.race.find_person_result = Mock(return_value=self.result1)
        self.race.find_person_by_bib = Mock(return_value=None)
        self.race.find_person_by_card = Mock(return_value=None)
        self.race.get_persons_by_group = Mock(return_value=[self.person1])
        
        for control in [self.control1, self.control2]:
            control.get_number_code = Mock(return_value=control.code)
    
      def teardown_method(self):
        
         if os.path.exists(self.test_file):
                 os.remove(self.test_file)
         if os.path.exists(self.test_file.replace('.sfrx', '.sfrx')):
                 os.remove(self.test_file.replace('.sfrx', '.sfrx'))
         os.rmdir(self.test_dir)
    
      @patch('sportorg.modules.sfr.sfrxexporter.memory')
      @patch('sportorg.modules.sfr.sfrxexporter.logging')
      @patch('sportorg.modules.sfr.sfrxexporter.translate')
      
      def test_export_sfrx_success(self, mock_translate, mock_logging, mock_memory):
   
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
  
        result = export_sfrx(self.test_file)
  
        assert result is True
        assert os.path.exists(self.test_file)
 
        with open(self.test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content) > 0
        
        mock_logging.info.assert_called()
    
      @patch('sportorg.modules.sfr.sfrxexporter.memory')
      @patch('sportorg.modules.sfr.sfrxexporter.logging')
      @patch('sportorg.modules.sfr.sfrxexporter.translate')
      def test_export_sfrx_no_race_data(self, mock_translate, mock_logging, mock_memory):
        """Тест экспорта без данных о гонке"""
        # Arrange
        mock_memory.race.return_value = None
        mock_translate.side_effect = lambda x: x
        
        # Act
        result = export_sfrx(self.test_file)
        
        # Assert
        assert result is False
        mock_logging.error.assert_called_with("No race data found")
    
      @patch('sportorg.modules.sfr.sfrxexporter.memory')
      @patch('sportorg.modules.sfr.sfrxexporter.logging')
      @patch('sportorg.modules.sfr.sfrxexporter.translate')
      def test_export_sfrx_with_relay(self, mock_translate, mock_logging, mock_memory):
        """Тест экспорта эстафеты"""
        # Arrange
        self.race.data.race_type = RaceType.RELAY
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
        
        # Act
        result = export_sfrx(self.test_file)
        
        # Assert
        assert result is True
        assert os.path.exists(self.test_file)
    
      @patch('sportorg.modules.sfr.sfrxexporter.memory')
      @patch('sportorg.modules.sfr.sfrxexporter.logging')
      @patch('sportorg.modules.sfr.sfrxexporter.translate')
      def test_export_sfrx_with_qualification(self, mock_translate, mock_logging, mock_memory):
        """Тест экспорта участника с квалификацией"""
        # Arrange
        self.person1.qual = Qualification.KMS
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
        
        # Act
        result = export_sfrx(self.test_file)
        
        # Assert
        assert result is True
        
        with open(self.test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Проверяем, что участник экспортирован
            assert "Иванов" in content
    
      @patch('sportorg.modules.sfr.sfrxexporter.memory')
      @patch('sportorg.modules.sfr.sfrxexporter.logging')
      @patch('sportorg.modules.sfr.sfrxexporter.translate')
      def test_export_sfrx_different_result_statuses(self, mock_translate, mock_logging, mock_memory):
        """Тест экспорта участников с разными статусами результатов"""
        # Arrange
        # Участник 2: DISQUALIFIED
        person2 = Mock(spec=Person)
        person2.id = uuid4()
        person2.name = "Петр"
        person2.surname = "Петров"
        person2.middle_name = ""
        person2.full_name = "Петров Петр"
        person2.bib = 102
        person2.group = self.group1
        person2.organization = self.org1
        person2.birth_date = date(1995, 3, 20)
        person2.year = 1995
        person2.qual = Qualification.NOT_QUALIFIED
        person2.comment = ""
        person2.start_time = OTime(10, 35, 0)
        person2.is_out_of_competition = False
        person2.is_rented_card = False
        person2.is_paid = False
        person2.is_personal = False
        person2.world_code = ""
        person2.national_code = 0
        person2.card_number = 123457
        person2.start_group = 0
        person2.result_count = 0
        
        result2 = Mock(spec=ResultSportident)
        result2.id = uuid4()
        result2.person = person2
        result2.start_time = OTime(10, 35, 0)
        result2.finish_time = OTime(11, 20, 0)
        result2.status = ResultStatus.DISQUALIFIED
        result2.status_comment = "Пропустил КП"
        result2.penalty_time = None
        result2.credit_time = None
        result2.penalty_laps = 0
        result2.place = 0
        result2.scores = 0
        result2.rogaine_score = 0
        result2.scores_ardf = 0
        result2.card_number = 123457
        result2.splits = []
        
        result2.get_start_time = Mock(return_value=OTime(10, 35, 0))
        result2.get_finish_time = Mock(return_value=OTime(11, 20, 0))
        result2.get_penalty_time = Mock(return_value=OTime())
        result2.get_credit_time = Mock(return_value=OTime())
        result2.is_status_ok = Mock(return_value=False)
        result2.is_sportident = Mock(return_value=True)
        
        # Участник 3: DID_NOT_START
        person3 = Mock(spec=Person)
        person3.id = uuid4()
        person3.name = "Сергей"
        person3.surname = "Сергеев"
        person3.middle_name = ""
        person3.full_name = "Сергеев Сергей"
        person3.bib = 103
        person3.group = self.group1
        person3.organization = self.org1
        person3.birth_date = date(1992, 7, 10)
        person3.year = 1992
        person3.qual = Qualification.NOT_QUALIFIED
        person3.comment = ""
        person3.start_time = None
        person3.is_out_of_competition = False
        person3.is_rented_card = False
        person3.is_paid = False
        person3.is_personal = False
        person3.world_code = ""
        person3.national_code = 0
        person3.card_number = 0
        person3.start_group = 0
        person3.result_count = 0
        
        result3 = Mock(spec=ResultSportident)
        result3.id = uuid4()
        result3.person = person3
        result3.start_time = None
        result3.finish_time = None
        result3.status = ResultStatus.DID_NOT_START
        result3.status_comment = "Не стартовал"
        result3.penalty_time = None
        result3.credit_time = None
        result3.penalty_laps = 0
        result3.place = 0
        result3.scores = 0
        result3.rogaine_score = 0
        result3.scores_ardf = 0
        result3.card_number = 0
        result3.splits = []
        
        result3.get_start_time = Mock(return_value=None)
        result3.get_finish_time = Mock(return_value=None)
        result3.get_penalty_time = Mock(return_value=OTime())
        result3.get_credit_time = Mock(return_value=OTime())
        result3.is_status_ok = Mock(return_value=False)
        result3.is_sportident = Mock(return_value=True)
   
        self.race.persons = [self.person1, person2, person3]
        self.race.results = [self.result1, result2, result3]
        
        def find_person_result_side_effect(person):
            if person.bib == 101:
                return self.result1
            elif person.bib == 102:
                return result2
            elif person.bib == 103:
                return result3
            return None
        
        self.race.find_person_result.side_effect = find_person_result_side_effect
        
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
       
        result = export_sfrx(self.test_file)
      
        assert result is True
        
        with open(self.test_file, 'r', encoding='utf-8') as f:
            content = f.read()
 
            assert "Иванов" in content
            assert "Петров" in content
            assert "Сергеев" in content
    
      @patch('sportorg.modules.sfr.sfrxexporter.memory')
      @patch('sportorg.modules.sfr.sfrxexporter.logging')
      @patch('sportorg.modules.sfr.sfrxexporter.translate')
      def test_export_sfrx_person_without_birth_date(self, mock_translate, mock_logging, mock_memory):
      
        self.person1.birth_date = None
        self.person1.year = 0
        
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
      
        result = export_sfrx(self.test_file)
      
        assert result is True
        
        with open(self.test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Иванов" in content
    
      @patch('sportorg.modules.sfr.sfrxexporter.memory')
      @patch('sportorg.modules.sfr.sfrxexporter.logging')
      @patch('sportorg.modules.sfr.sfrxexporter.translate')
      def test_export_sfrx_person_without_result(self, mock_translate, mock_logging, mock_memory):
   
        self.race.find_person_result.return_value = None
        
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
       
        result = export_sfrx(self.test_file)
     
        assert result is True
        
        with open(self.test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Иванов" in content
    
      @patch('sportorg.modules.sfr.sfrxexporter.memory')
      @patch('sportorg.modules.sfr.sfrxexporter.logging')
      @patch('sportorg.modules.sfr.sfrxexporter.translate')
      def test_export_sfrx_with_multiple_organizations(self, mock_translate, mock_logging, mock_memory):
  
        org2 = Mock(spec=Organization)
        org2.name = "Динамо"
        
        org3 = Mock(spec=Organization)
        org3.name = "Спартак"
        
        self.race.organizations = [self.org1, org2, org3]
        
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
       
        result = export_sfrx(self.test_file)
      
        assert result is True
    
      @patch('sportorg.modules.sfr.sfrxexporter.memory')
      @patch('sportorg.modules.sfr.sfrxexporter.logging')
      @patch('sportorg.modules.sfr.sfrxexporter.translate')
      def test_export_sfrx_with_special_control_codes(self, mock_translate, mock_logging, mock_memory):
        """Тест экспорта со специальными кодами КП"""
        # Arrange
        # Добавляем КП с кодами 240, 241, 242 (старт, финиш и т.д.)
        control3 = Mock(spec=CourseControl)
        control3.code = "240"
        control3.length = 0
        control3.get_number_code = Mock(return_value="240")
        
        control4 = Mock(spec=CourseControl)
        control4.code = "241"
        control4.length = 0
        control4.get_number_code = Mock(return_value="241")

        control5 = Mock(spec=CourseControl)
        control5.code = "A"
        control5.length = 0
        control5.get_number_code = Mock(return_value="0")
        
        self.course1.controls = [self.control1, self.control2, control3, control4, control5]
        
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
      
        result = export_sfrx(self.test_file)
       
        assert result is True
    
      @patch('sportorg.modules.sfr.sfrxexporter.memory')
      @patch('sportorg.modules.sfr.sfrxexporter.logging')
      def test_export_sfrx_file_structure(self, mock_logging, mock_memory):
     
        mock_memory.race.return_value = self.race
    
        result = export_sfrx(self.test_file)
        
        assert result is True
        
        with open(self.test_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
          
        content = "".join(lines)
     
        assert "SFRx_v2404" in content  # Заголовок
        assert "p1" in content  # Дни
        assert "h0" in content  # Федерации
        assert "f0" in content  # Клубы
        assert "g" in content  # Группы
        assert "t" in content  # Команды
        assert "d" in content  # Дистанции
        assert "k" in content  # КП
        assert "c" in content  # Участники
    
      @patch('sportorg.modules.sfr.sfrxexporter.memory')
      @patch('sportorg.modules.sfr.sfrxexporter.logging')
      @patch('sportorg.modules.sfr.sfrxexporter.translate')
      def test_export_sfrx_exception_handling(self, mock_translate, mock_logging, mock_memory):
  
        mock_memory.race.return_value = self.race
        mock_translate.side_effect = lambda x: x
        
        with patch('builtins.open', side_effect=Exception("Test error")):
    
            result = export_sfrx(self.test_file)
     
            assert result is False
            mock_logging.error.assert_called()


class TestSFRExporter:
    """Тесты для функции-обертки export_sfr_data"""
    
    @patch('sportorg.modules.sfr.sfrexporter.memory')
    @patch('sportorg.modules.sfr.sfrexporter.logging')
    @patch('sportorg.modules.sfr.sfrexporter.translate')
    def test_export_sfr_data_file_type(self, mock_translate, mock_logging, mock_memory):
          
        from sportorg.modules.sfr.sfrexporter import export_sfr_data
        
        race = Mock(spec=Race)
        mock_memory.race.return_value = race
        mock_translate.side_effect = lambda x: x
     
        with patch('sportorg.modules.sfr.sfrexporter.export_sfrx') as mock_export_sfrx:
            mock_export_sfrx.return_value = True
          
            result = export_sfr_data("test.sfrx", export_type='file')
        
            assert result is True
            mock_export_sfrx.assert_called_once_with("test.sfrx")
    
    @patch('sportorg.modules.sfr.sfrexporter.memory')
    @patch('sportorg.modules.sfr.sfrexporter.logging')
    @patch('sportorg.modules.sfr.sfrexporter.translate')
    def test_export_sfr_data_no_race(self, mock_translate, mock_logging, mock_memory):
        """Тест экспорта без данных о гонке"""
     
        from sportorg.modules.sfr.sfrexporter import export_sfr_data
        
        mock_memory.race.return_value = None
        mock_translate.side_effect = lambda x: x
        
        result = export_sfr_data("test.sfrx", export_type='file')
        
        assert result is False
        mock_logging.error.assert_called_with("No race data found")
    
    @patch('sportorg.modules.sfr.sfrexporter.memory')
    @patch('sportorg.modules.sfr.sfrexporter.translate')
    def test_export_sfr_data_invalid_type(self, mock_translate, mock_memory):
        """Тест экспорта с неверным типом"""

        from sportorg.modules.sfr.sfrexporter import export_sfr_data
        
        race = Mock(spec=Race)
        mock_memory.race.return_value = race
        mock_translate.side_effect = lambda x: x
        
        result = export_sfr_data("test.sfrx", export_type='invalid')
        
        assert result is False


from sportorg.modules.sfr.sfrxexporter import export_sfrx


if __name__ == "__main__":
    pytest.main([__file__, "-v"])