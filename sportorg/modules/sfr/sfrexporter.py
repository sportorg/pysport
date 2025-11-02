# sfrexporter.py
import logging
from datetime import datetime

from sportorg.language import translate
from sportorg.models import memory
from sportorg.models.memory import ResultStatus


def export_sfr_data(destination: str, export_type='file'):
    """
    Главная функция экспорта данных в SFR формат
    export_type: 'file' - экспорт в файл, 'card' - запись на карту
    """
    race = memory.race()
    if not race:
        logging.error(translate("No race data found"))
        return False
    
    if export_type == 'file':
        from sportorg.modules.sfr.sfrxexporter import export_sfrx
        return export_sfrx(destination)
    
    elif export_type == 'card':
        from sportorg.modules.sfr.sfrwriter import write_to_sfr_card
        
        # Получаем данные для записи на карту
        # В реальной реализации здесь должен быть выбор участника
        card_data = _prepare_card_data(race)
        return write_to_sfr_card(card_data)
    
    return False


def _prepare_card_data(race):
    """
    Подготовка данных для записи на SFR-карту
    В реальной реализации здесь должен быть интерфейс выбора участника
    """
    # Пример данных - берем первого участника с результатом
    for person in race.persons:
        result = race.find_person_result(person)
        if result and result.start_time:
            card_data = {
                'card_number': person.card_number or 0,
                'bib': person.bib or 0,
                'start_time': result.start_time,
                'finish_time': result.finish_time,
                'punches': []
            }
            
            # Добавляем отметки
            if result.splits:
                for split in result.splits:
                    if split.code and split.time:
                        card_data['punches'].append({
                            'code': split.code,
                            'time': split.time
                        })
            
            return card_data
    
    return None