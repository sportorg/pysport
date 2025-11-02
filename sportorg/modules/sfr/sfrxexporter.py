# sfrxexporter.py
import logging
from datetime import datetime

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
        with open(destination, 'w', encoding='UTF-8') as f:
            # Заголовок файла SFRx - ВАЖНО: точно как в примере
            _write_header(f, race)
            
            # Дни соревнований
            _write_days(f, race)
            
            # Федерации
            _write_federations(f)
            
            # Клубы  
            _write_clubs(f)
            
            # Группы - ВАЖНО: правильное количество полей
            _write_groups(f, race)
            
            # Команды
            _write_teams(f, race)
            
            # Дистанции
            _write_courses(f, race)
            
            # Контрольные пункты
            _write_controls(f, race)
            
            # Участники - ВАЖНО: правильное количество полей
            _write_competitors(f, race)
            
            # Отметки (сплиты)
            _write_splits(f, race)
            
        logging.info(translate("Export completed successfully to {}").format(destination))
        return True
        
    except Exception as e:
        logging.error(translate("Export error: {}").format(str(e)))
        return False


def _write_header(f, race: Race):
    """Запись заголовка файла - ТОЧНО как в примере"""
    title = race.data.title or "Competition"
    location = race.data.location or ""
    days = 1
    
    # Организаторы - берем из настроек или используем заглушки
    organizer = getattr(race.data, 'organizer', 'Долгов Е.Н.') or 'Долгов Е.Н.'
    secretary = getattr(race.data, 'secretary', 'Степанов П.Н.') or 'Степанов П.Н.'
    
    # Тип соревнования
    race_type = "Индивидуальные"
    if race.data.race_type and hasattr(race.data.race_type, 'value'):
        if race.data.race_type.value == "relay":
            race_type = "Эстафета"
    
    # ВАЖНО: точно 8 полей как в примере, включая пустые
    header_line = "SFRx_v2404\t{}\t{}\t{}\t\t\t\t{}\n".format(
        title, location, days, race_type
    )
    f.write(header_line)


def _write_days(f, race: Race):
    """Запись информации о днях соревнований"""
    start_date = race.data.start_datetime or datetime.now()
    date_str = start_date.strftime("%d.%m.%Y")
    discipline = "Кросс - спринт"
    
    # ВАЖНО: только 4 поля как в примере
    day_line = "p1\t{}\t{}\t\n".format(discipline, date_str)
    f.write(day_line)


def _write_federations(f):
    """Запись информации о федерациях"""
    federation_line = "h0\tРегиональная ОО ФСО\n"
    f.write(federation_line)


def _write_clubs(f):
    """Запись информации о клубах"""
    club_line = "f0\tЭкстрим парк\n"
    f.write(club_line)


def _write_groups(f, race: Race):
    """Запись информации о группах - ВАЖНО: 13 полей"""
    for i, group in enumerate(race.groups):
        group_id = str(i).zfill(5)
        group_name = group.name or f"Group_{i}"
        
        # Находим связанную дистанцию
        course_index = 0
        if group.course and group.course in race.courses:
            course_index = race.courses.index(group.course)
        
        # ВАЖНО: ровно 13 полей как в примере
        group_line = "g{}\t{}\t-1\t0\t0\t\t150\t{}\t0\t0\t0\t5400000\t0\t\n".format(
            group_id,
            group_name,
            course_index
        )
        f.write(group_line)


def _write_teams(f, race: Race):
    """Запись информации о командах - ВАЖНО: 7 полей"""
    for i, org in enumerate(race.organizations):
        team_id = str(i).zfill(5)
        team_name = org.name or f"Team_{i}"
        
        # ВАЖНО: ровно 7 полей как в примере
        team_line = "t{}\t{}\t-1\t\t\t\t0\t\n".format(team_id, team_name)
        f.write(team_line)


def _write_courses(f, race: Race):
    """Запись информации о дистанциях"""
    for i, course in enumerate(race.courses):
        course_id = str(i).zfill(5)
        course_name = course.name or f"Course_{i}"
        
        # Формируем строку контролов - пары код/длина
        controls_str = ""
        if course.controls:
            for control in course.controls:
                if str(control.code).isdigit() and control.code not in ['240', '241', '242']:
                    controls_str += "\t{}\t{}".format(control.code, control.length or "0")
        
        # ВАЖНО: правильное количество основных полей + пары контролов
        course_line = "d{}\t{}\t{}\t1\t0\t0\t{}\t{}\t{}".format(
            course_id,
            course_name,
            course.bib or "0",  # bib дистанции
            course.length or "0",  # длина
            course.climb or "0",   # набор высоты
            controls_str
        )
        f.write(course_line + "\n")


def _write_controls(f, race: Race):
    """Запись информации о контрольных пунктах - ВАЖНО: 7 полей"""
    # Собираем все уникальные коды контролов
    control_codes = set()
    for course in race.courses:
        for control in course.controls:
            if str(control.code).isdigit() and control.code not in ['240', '241', '242']:
                control_codes.add(control.code)
    
    # Сортируем и выводим
    for i, code in enumerate(sorted(control_codes, key=int)):
        control_id = str(i).zfill(5)
        # ВАЖНО: ровно 7 полей как в примере
        control_line = "k{}\t{}\t{}\t0\t0\t0\t-1\t\n".format(control_id, code, code)
        f.write(control_line)


def _write_competitors(f, race: Race):
    """Запись информации об участниках - ВАЖНО: 19 полей"""
    for i, person in enumerate(race.persons):
        person_id = str(i).zfill(5)
        
        # Определяем группу
        group_id = "0"
        if person.group and person.group in race.groups:
            group_id = str(race.groups.index(person.group))
        
        # Определяем команду
        team_id = "0"
        if person.organization and person.organization in race.organizations:
            team_id = str(race.organizations.index(person.organization))
        
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
        
        # Время старта
        start_time = ""
        if result and result.start_time:
            start_time = _format_time(result.start_time)
        elif person.start_time:
            start_time = _format_time(person.start_time)
        
        # Время финиша
        finish_time = ""
        if result and result.finish_time:
            finish_time = _format_time(result.finish_time)
        
        # Результат
        result_status = ""
        result_time = ""
        if result:
            if result.status == ResultStatus.DISQUALIFIED:
                result_status = "cнят"
            elif result.status == ResultStatus.OVERTIME:
                result_status = "cнят (к/в)"
            elif result.status == ResultStatus.DID_NOT_START:
                result_status = "н/с"
            elif result.finish_time and result.start_time:
                # Рассчитываем время результата
                result_time = _calculate_result_time(result.start_time, result.finish_time)
        
        # Полное имя (только имя и фамилия как в примере)
        full_name = "{} {}".format(
            person.surname or "", 
            person.name or ""
        ).strip()
        
        # ВАЖНО: ровно 19 полей как в примере
        competitor_line = "c{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
            person_id,
            person.bib or "0",      # 1. номер
            group_id,               # 2. группа
            person.surname or "",   # 3. фамилия
            full_name,              # 4. полное имя
            team_id,                # 5. команда
            year,                   # 6. год рождения
            birthday,               # 7. дата рождения
            qual_id,                # 8. квалификация
            person.comment or "",   # 9. комментарий
            "0",                    # 10. аренда карты
            "150",                  # 11. стартовый взнос
            "0",                    # 12. оплачено
            "0",                    # 13. дата оплаты
            start_time,             # 14. время старта
            finish_time,            # 15. время финиша
            "",                     # 16. кредитное время (пустое)
            result_time or result_status,  # 17. результат/статус
            "0",                    # 18. нули
            "0"                     # 19. нули
        )
        f.write(competitor_line)


def _write_splits(f, race: Race):
    """Запись информации об отметках на КП"""
    split_id = 0
    
    for person in race.persons:
        result = race.find_person_result(person)
        if not result or not result.splits:
            continue
        
        # Сортируем сплиты по времени
        sorted_splits = sorted(
            [s for s in result.splits if s.time], 
            key=lambda x: x.time
        )
        
        if not sorted_splits:
            continue
            
        splits_str = ""
        order = 1
        
        # Добавляем старт если есть
        if result.start_time:
            start_time = _format_time(result.start_time)
            splits_str += "\t241\t0\t{}".format(start_time)
        
        # Добавляем контрольные пункты
        for split in sorted_splits:
            if split.code and split.time and str(split.code) not in ['240', '241', '242']:
                time_str = _format_time(split.time)
                splits_str += "\t{}\t{}\t{}".format(split.code, order, time_str)
                order += 1
        
        # Добавляем финиш если есть
        if result.finish_time:
            finish_time = _format_time(result.finish_time)
            splits_str += "\t240\t0\t{}".format(finish_time)
        
        if splits_str:
            split_line = "s{}\t{}\t\t\t1\t128{}\n".format(
                str(split_id).zfill(5),
                person.bib or "0",
                splits_str
            )
            f.write(split_line)
            split_id += 1


def _format_time(dt):
    """Форматирование времени в HH:MM:SS"""
    if hasattr(dt, 'strftime'):
        return dt.strftime("%H:%M:%S")
    elif hasattr(dt, 'str'):
        return str(dt)
    return ""


def _calculate_result_time(start_time, finish_time):
    """Расчет времени результата"""
    try:
        if hasattr(start_time, 'timestamp') and hasattr(finish_time, 'timestamp'):
            time_diff = finish_time - start_time
            total_seconds = int(time_diff.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
    except:
        pass
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