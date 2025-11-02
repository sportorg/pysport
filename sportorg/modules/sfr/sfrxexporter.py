# sfrxexporter.py
import os
import logging
from datetime import datetime, time

from sportorg.language import translate
from sportorg.models import memory
from sportorg.models.memory import (
    Qualification,
    Race,
    ResultStatus,
)


def export_sfrx(destination: str):
    """
    Экспорт данных из SportOrg в формат SFRx
    """
    race = memory.race()
    if not race:
        logging.error(translate("No race data found"))
        return False

    try:
        # Важно: открываем без BOM и с табуляцией как разделитель
        base_name = os.path.splitext(destination)[0]
        with open(base_name + '.sfrx', 'w', encoding='utf-8', newline='') as f:
        
 #       with open(destination, 'w', encoding='utf-8', newline='') as f:
            # Заголовок файла SFRx
            _write_header(f, race)
            
            # Дни соревнований
            _write_days(f, race)
            
            # Федерации
            _write_federations(f)
            
            # Клубы  
            _write_clubs(f)
            
            # Группы
            _write_groups(f, race)
            
            # Команды
            _write_teams(f, race)
            
            # Дистанции
            _write_courses(f, race)
            
            # Контрольные пункты
            _write_controls(f, race)
            
            # Участники
            _write_competitors(f, race)
            
            # Отметки (сплиты)
            _write_splits(f, race)
            
        logging.info(translate("Export completed successfully to {}").format(destination))
        return True
        
    except Exception as e:
        logging.error(translate("Export error: {}").format(str(e)))
        return False


def _write_header(f, race: Race):
    """Запись заголовка файла - исправленная версия"""
    title = race.data.title or "Competition"
    location = race.data.location or ""
    
    # Получаем организатора из доступных атрибутов
    organizer = ""
    if hasattr(race.data, 'organizer') and race.data.organizer:
        organizer = race.data.organizer
    elif hasattr(race.data, 'organization') and race.data.organization:
        organizer = race.data.organization
    
    days = 1
    
    # Тип соревнования
    race_type = "Индивидуальные"
    if race.data.race_type and hasattr(race.data.race_type, 'value'):
        if race.data.race_type.value == "relay":
            race_type = "Эстафета"
    
    # Полный заголовок согласно формату SFRx
    header_fields = [
        "SFRx_v2404",
        title,
        location,
        str(days),
        "", "", "",  # пустые поля
        race_type,
        organizer,
        "", "", "", "", "",  # дополнительные пустые поля
        "SportOrg Export"  # источник данных
    ]
    f.write("\t".join(header_fields) + "\n")


def _write_days(f, race: Race):
    """Запись информации о днях соревнований"""
    start_date = race.data.start_datetime or datetime.now()
    date_str = start_date.strftime("%d.%m.%Y")
    
    # Определяем дисциплину на основе типа гонки
    discipline = "Кросс - спринт"
    if race.data.race_type and hasattr(race.data.race_type, 'value'):
        if race.data.race_type.value == "relay":
            discipline = "Эстафета"
        elif race.data.race_type.value == "skiing":
            discipline = "Лыжные гонки"
    
    day_fields = [
        "p1",
        discipline,
        date_str,
        ""  # пустое поле в конце
    ]
    f.write("\t".join(day_fields) + "\n")


def _write_federations(f):
    """Запись информации о федерациях"""
    federation_fields = [
        "h0", 
        "Региональная ОО ФСО"
    ]
    f.write("\t".join(federation_fields) + "\n")


def _write_clubs(f):
    """Запись информации о клубах"""
    club_fields = [
        "f0",
        "Экстрим парк"
    ]
    f.write("\t".join(club_fields) + "\n")


def _write_groups(f, race: Race):
    """Запись информации о группах"""
    for i, group in enumerate(race.groups):
        # ID группы в формате g00000, g00001, etc.
        group_id_str = str(i).zfill(5)
        group_name = group.name or f"Group_{i}"
        
        course_index = "0"
        if group.course and group.course in race.courses:
            course_index = str(race.courses.index(group.course))
        
        group_fields = [
            f"g{group_id_str}",
            group_name,
            "-1", "0", "0",
            "",  # пустое поле
            "150",  # стартовый взнос
            course_index,
            "0", "0", "0",
            "5400000",  # контрольное время (90 минут)
            "0",
            ""  # пустое поле в конце
        ]
        f.write("\t".join(group_fields) + "\n")


def _write_teams(f, race: Race):
    """Запись информации о командах"""
    for i, org in enumerate(race.organizations):
        # ID команды в формате t00000, t00001, etc.
        team_id_str = str(i).zfill(5)
        team_name = org.name or f"Team_{i}"
        
        team_fields = [
            f"t{team_id_str}",
            team_name,
            "-1", "", "", "",
            "0",
            ""  # пустое поле в конце
        ]
        f.write("\t".join(team_fields) + "\n")


def _write_courses(f, race: Race):
    """Запись информации о дистанциях"""
    for i, course in enumerate(race.courses):
        # ID дистанции в формате d00000, d00001, etc.
        course_id_str = str(i).zfill(5)
        course_name = course.name or f"Course_{i}"
        
        # Формируем пары код/длина для контролов
        control_pairs = []
        if course.controls:
            for control in course.controls:
                code_str = str(control.code)
                if code_str.isdigit() and code_str not in ['240', '241', '242']:
                    control_pairs.extend([code_str, str(control.length or "0")])
        
        course_fields = [
            f"d{course_id_str}",
            course_name,
            str(course.bib or "0"),  # номер дистанции для эстафеты
            "1", #  
            "0", #
            "0",  #
            str(course.length or "0"),  # длина дистанции
            str(course.climb or "0"),  # набор высоты
            str(len(control_pairs) // 2)  # количество КП
        ]
        
        # Добавляем пары контролов
        course_fields.extend(control_pairs)
        
        f.write("\t".join(course_fields) + "\n")


def _write_controls(f, race: Race):
    """Запись информации о контрольных пунктах"""
    # Собираем все уникальные коды контролов
    control_codes = set()
    for course in race.courses:
        for control in course.controls:
            code_str = str(control.code)
            if code_str.isdigit() and code_str not in ['240', '241', '242']:
                control_codes.add(int(code_str))
    
    for i, code in enumerate(sorted(control_codes)):
        # ID контрольного пункта в формате k00000, k00001, etc.
        control_id_str = str(i).zfill(5)
        
        control_fields = [
            f"k{control_id_str}",
            str(code),
            str(code),
            "0", "0", "0",
            "-1",
            ""  # пустое поле в конце
        ]
        f.write("\t".join(control_fields) + "\n")


def _write_competitors(f, race: Race):
    """Запись информации об участниках"""
    for i, person in enumerate(race.persons):
        # ID участника в формате c00000, c00001, etc.
        person_id_str = str(i).zfill(5)
        
        # Определяем группу
        group_id = "0"
        if person.group:
            for idx, group in enumerate(race.groups):
                if group == person.group:
                    group_id = str(idx)
                    break
        
        # Определяем команду
        team_id = "0"
        if person.organization:
            for idx, org in enumerate(race.organizations):
                if org == person.organization:
                    team_id = str(idx)
                    break
        
        # Год рождения
        year = ""
        if person.year:
            year = str(person.year)
        elif person.birth_date:
            year = person.birth_date.strftime("%Y")
        
        birthday = person.birth_date.strftime("%d.%m.%Y") if person.birth_date else ""
        
        # Квалификация
        qual_id = sportorg_qual_to_sfr(person.qual) if person.qual else "0"
        
        # Результаты
        result = race.find_person_result(person)
        
        # Время старта (абсолютное)
        start_time = ""
        if result and result.start_time:
            start_time = _format_time(result.start_time)
        elif person.start_time:
            start_time = _format_time(person.start_time)
        
        # Время финиша (абсолютное)
        finish_time = ""
        if result and result.finish_time:
            finish_time = _format_time(result.finish_time)
        
        # Результат - берем напрямую из результата, если есть
        result_status = ""
        result_time = ""
        if result:
            # Пробуем получить результат напрямую из объекта результата
            if hasattr(result, 'result') and result.result:
                result_time = _format_time(result.result)
            elif hasattr(result, 'get_result') and callable(result.get_result):
                result_time_obj = result.get_result()
                if result_time_obj:
                    result_time = _format_time(result_time_obj)
            elif result.status == ResultStatus.OK:
                # Если прямого результата нет, но статус ОК, рассчитываем
                if result.finish_time and result.start_time:
                    result_time = _calculate_result_time(result.start_time, result.finish_time)
            elif result.status == ResultStatus.DISQUALIFIED:
                result_status = "cнят"
            elif result.status == ResultStatus.OVERTIME:
                result_status = "cнят (к/в)"
            elif result.status == ResultStatus.DID_NOT_FINISH:
                result_status = "снят"
            elif result.status == ResultStatus.DID_NOT_START:
                result_status = "н/с"
            elif result.status == ResultStatus.MISSING_PUNCH:
                result_status = "снят"
        
        # Полное имя
        surname = person.surname or ""
        first_name = person.name or ""
        
        competitor_fields = [
            f"c{person_id_str}",
            str(person.bib or "0"),
            group_id,
            surname,
            first_name,
            team_id,
 #          "",  # год рождения (пустое поле)
            birthday,
            qual_id,
            person.comment or "",
 #           "",  # пустое поле
            "0",  # аренда карты
            "150",  # стартовый взнос
            "0",  # оплачено
            "0",  # дата оплаты
            start_time,      # абсолютное время старта
            finish_time,     # абсолютное время финиша
            result_time or result_status,  # относительное время результата
            "",  # кредитное время
            "0", "0", "0"  # нули в конце
        ]
        f.write("\t".join(competitor_fields) + "\n")


def _write_splits(f, race: Race):
    """Запись информации об отметках на КП"""
    split_id = 0
    
    for person in race.persons:
        result = race.find_person_result(person)
        if not result or not result.splits:
            continue
        
        # Получаем время старта для фильтрации
        start_time = None
        if result.start_time:
            start_time = result.start_time
        elif person.start_time:
            start_time = person.start_time
        
        # Фильтруем сплиты: только после времени старта и обычные КП
        valid_splits = []
        for split in result.splits:
            if (split.time and split.code and 
                str(split.code) not in ['240', '241', '242']):
                # Если известно время старта, фильтруем по нему
                if start_time is None or split.time >= start_time:
                    valid_splits.append(split)
        
        # Сортируем отфильтрованные сплиты по времени
        sorted_splits = sorted(valid_splits, key=lambda x: x.time)
        
        if not sorted_splits:
            continue
            
        split_data = []
        
        # Добавляем старт если есть реальная отметка 241
        start_split = next((s for s in result.splits if str(s.code) == '241' and s.time), None)
        if start_split:
            start_time_str = _format_time(start_split.time)
            split_data.extend(["241", "0", start_time_str])
        
        # Добавляем контрольные пункты в правильном порядке
        for i, split in enumerate(sorted_splits):
            code_str = str(split.code)
            time_str = _format_time(split.time)
            split_data.extend([code_str, str(i + 1), time_str])
        
        # Добавляем финиш если есть реальная отметка 240
        finish_split = next((s for s in result.splits if str(s.code) == '240' and s.time), None)
        if finish_split:
            finish_time_str = _format_time(finish_split.time)
            split_data.extend(["240", "0", finish_time_str])
        
        if split_data:
            split_id_str = str(split_id).zfill(5)
            split_fields = [
                f"s{split_id_str}",
                str(person.bib or "0"),  # Используем номер участника (bib), а не ID
                "", "",  # пустые поля
                "1",
                "128"
            ]
            split_fields.extend(split_data)
            f.write("\t".join(split_fields) + "\n")
            split_id += 1

def _format_time(dt):
    """Форматирование времени для различных типов объектов с секундами"""
    if not dt:
        return ""
    
    try:
        # Если это datetime объект
        if hasattr(dt, 'strftime'):
            return dt.strftime("%H:%M:%S")
        
        # Если это time объект
        elif hasattr(dt, 'hour') and hasattr(dt, 'minute') and hasattr(dt, 'second'):
            return f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"
        
        # Если это OTime объект - пробуем получить часы, минуты, секунды через getattr
        elif hasattr(dt, 'hour') or hasattr(dt, 'minute'):
            hour = getattr(dt, 'hour', 0)
            minute = getattr(dt, 'minute', 0)
            second = getattr(dt, 'second', 0)
            return f"{hour:02d}:{minute:02d}:{second:02d}"
        
        # Если это строка
        elif isinstance(dt, str):
            return dt
            
    except Exception as e:
        logging.debug(f"Time formatting error for {type(dt)}: {e}")
    
    return ""

def _convert_to_datetime(time_obj):
    """Конвертирует различные типы времени в datetime"""
    if not time_obj:
        return None
    
    try:
        # Если уже datetime
        if hasattr(time_obj, 'strftime') and hasattr(time_obj, 'date'):
            return time_obj
        
        # Если это time объект
        elif hasattr(time_obj, 'hour') and hasattr(time_obj, 'minute') and hasattr(time_obj, 'second'):
            return datetime.combine(datetime.today().date(), 
                                  time(hour=time_obj.hour, minute=time_obj.minute, second=time_obj.second))
        
        # Если это OTime объект с методом to_datetime
        elif hasattr(time_obj, 'to_datetime'):
            return time_obj.to_datetime()
        
        # Если это OTime объект - создаем time из атрибутов
        elif hasattr(time_obj, 'hour') or hasattr(time_obj, 'minute'):
            hour = getattr(time_obj, 'hour', 0)
            minute = getattr(time_obj, 'minute', 0)
            second = getattr(time_obj, 'second', 0)
            return datetime.combine(datetime.today().date(), 
                                  time(hour=hour, minute=minute, second=second))
    
    except Exception as e:
        logging.debug(f"Time conversion error: {e}")
    
    return None

def _calculate_result_time(start_time, finish_time):
    """Расчет времени результата"""
    try:
        # Конвертируем в datetime для точного расчета
        start_dt = _convert_to_datetime(start_time)
        finish_dt = _convert_to_datetime(finish_time)
        
        if start_dt and finish_dt:
            # Убедимся, что оба времени в один день
            if finish_dt < start_dt:
                # Если финиш раньше старта (после полуночи), добавляем 1 день
                finish_dt = finish_dt.replace(day=finish_dt.day + 1)
            
            time_diff = finish_dt - start_dt
            total_seconds = int(time_diff.total_seconds())
            
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
    except Exception as e:
        logging.debug(f"Result time calculation error: {e}")
    
    return ""

def sportorg_qual_to_sfr(qual: Qualification) -> str:
    """Конвертация квалификации из SportOrg в SFR"""
    if not qual:
        return "0"
    
    qual_value = qual.value if hasattr(qual, 'value') else int(qual)
    
    return {
        0: "0",   # No qualification
        1: "3",   # MSIC
        2: "2",   # MS
        3: "1",   # KMS
        4: "6",   # I
        5: "5",   # II
        6: "4",   # III
        7: "7",   # Iю
        8: "8",   # IIю
        9: "9",   # IIIю
    }.get(qual_value, "0")