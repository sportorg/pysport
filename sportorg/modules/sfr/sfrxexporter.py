# sfrxexporter.py
import logging
from datetime import datetime

from sportorg.language import translate
from sportorg.models import memory
from sportorg.models.memory import (
    Qualification,
    Race,
    ResultStatus,
    ResultSFR,
    SystemType,
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
            # Заголовок файла SFRx
            _write_header(f, race)
            
            # Дни соревнований
            _write_days(f, race)
            
            # Дистанции
            _write_courses(f, race)
            
            # Группы
            _write_groups(f, race)
            
            # Команды
            _write_teams(f, race)
            
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
    """Запись заголовка файла"""
    title = race.data.title or "Competition"
    location = race.data.location or ""
    days = 1  # По умолчанию 1 день
    
    # Определяем тип соревнования
    race_type = "Гонка"  # По умолчанию индивидуальная гонка
    if race.data.race_type and hasattr(race.data.race_type, 'value'):
        if race.data.race_type.value == "relay":
            race_type = "Эстафета"
    
    header_line = "SFRx\t{}\t{}\t{}\t\t\t\t{}\n".format(title, location, days, race_type)
    f.write(header_line)


def _write_days(f, race: Race):
    """Запись информации о днях соревнований"""
    # Для упрощения считаем 1 день
    start_date = race.data.start_datetime or datetime.now()
    date_str = start_date.strftime("%d.%m.%Y")
    
    day_line = "p1\t{}\t{}\t\n".format("Дистанция", date_str)
    f.write(day_line)


def _write_courses(f, race: Race):
    """Запись информации о дистанциях"""
    for i, course in enumerate(race.courses):
        course_id = i + 1
        
        # Формируем строку контролов
        controls_str = ""
        for control in course.controls:
            controls_str += "\t{}\t{}".format(control.code, control.length or "0")
        
        course_line = "d{}\t{}\t{}\t1\t\t\t{}\t{}\t{}".format(
            course_id,
            course.name or f"Course_{course_id}",
            course.bib or "0",
            course.length or "0",
            course.climb or "0",
            controls_str
        )
        f.write(course_line + "\n")


def _write_groups(f, race: Race):
    """Запись информации о группах"""
    for i, group in enumerate(race.groups):
        group_id = i + 1
        
        # Находим связанную дистанцию
        course_index = -1
        if group.course and group.course in race.courses:
            course_index = race.courses.index(group.course) + 1
        
        # Для каждого дня указываем дистанцию (в упрощенной версии - только 1 день)
        course_for_day = str(course_index) if course_index > 0 else "-1"
        
        group_line = "g{}\t{}\t\t\t\t\t\t{}".format(
            group_id,
            group.name or f"Group_{group_id}",
            course_for_day
        )
        f.write(group_line + "\n")


def _write_teams(f, race: Race):
    """Запись информации о командах"""
    for i, org in enumerate(race.organizations):
        team_id = i + 1
        team_line = "t{}\t{}\n".format(team_id, org.name or f"Team_{team_id}")
        f.write(team_line)


def _write_competitors(f, race: Race):
    """Запись информации об участниках"""
    for i, person in enumerate(race.persons):
        person_id = i + 1
        
        # Определяем группу
        group_id = "0"
        if person.group and person.group in race.groups:
            group_id = str(race.groups.index(person.group) + 1)
        
        # Определяем команду
        team_id = "0"
        if person.organization and person.organization in race.organizations:
            team_id = str(race.organizations.index(person.organization) + 1)
        
        # Год рождения
        year = ""
        if person.year:
            year = str(person.year)
        elif person.birth_date:
            year = person.birth_date.strftime("%Y")
        
        # Дата рождения в формате ДД.ММ.ГГГГ
        birthday = ""
        if person.birth_date:
            birthday = person.birth_date.strftime("%d.%m.%Y")
        
        # Квалификация
        qual_id = sportorg_qual_to_sfr(person.qual) if person.qual else "0"
        
        # Результаты
        result = race.find_person_result(person)
        
        # Время старта
        start_time = ""
        if result and result.start_time:
            start_time = result.start_time.strftime("%H:%M:%S") if hasattr(result.start_time, 'strftime') else str(result.start_time)
        elif person.start_time:
            start_time = person.start_time.strftime("%H:%M:%S") if hasattr(person.start_time, 'strftime') else str(person.start_time)
        
        # Время финиша
        finish_time = ""
        if result and result.finish_time:
            finish_time = result.finish_time.strftime("%H:%M:%S") if hasattr(result.finish_time, 'strftime') else str(result.finish_time)
        
        # Кредитное время
        credit_time = ""
        if result and result.credit_time:
            credit_time = result.credit_time.strftime("%H:%M:%S") if hasattr(result.credit_time, 'strftime') else str(result.credit_time)
        
        # Результат (статус)
        result_status = ""
        if result:
            if result.status == ResultStatus.DISQUALIFIED:
                result_status = "cнят"
            elif result.status == ResultStatus.OVERTIME:
                result_status = "cнят (к/в)"
            elif result.status == ResultStatus.DID_NOT_START:
                result_status = "н/с"
            elif result.finish_time and result.start_time:
                # Рассчитываем время результата
                try:
                    result_time = result.finish_time - result.start_time
                    result_status = str(result_time)
                except:
                    result_status = ""
        
        # Формируем строку участника
        competitor_line = "c{}\t{}\t{}\t{}\t{} {}\t{}\t{}\t{}\t{}\t\t\t{}\t{}\t{}\t{}\t{}\n".format(
            person_id,
            person.bib or "0",
            group_id,
            person.surname or "",
            person.name or "",
            person.middle_name or "",
            team_id,
            year,
            birthday,
            qual_id,
            person.comment or "",
            start_time,
            finish_time,
            credit_time,
            result_status
        )
        f.write(competitor_line)


def _write_splits(f, race: Race):
    """Запись информации об отметках на КП"""
    split_id = 1
    
    for person in race.persons:
        result = race.find_person_result(person)
        if not result or not result.splits:
            continue
        
        # Сортируем сплиты по времени
        sorted_splits = sorted(result.splits, key=lambda x: x.time)
        
        splits_str = ""
        for split in sorted_splits:
            if split.code and split.time:
                time_str = split.time.strftime("%H:%M:%S") if hasattr(split.time, 'strftime') else str(split.time)
                splits_str += "\t{}\t\t{}".format(split.code, time_str)
        
        if splits_str:
            split_line = "s{}\t{}\t\t\t1\t{}".format(
                split_id,
                person.bib or "0",
                splits_str
            )
            f.write(split_line + "\n")
            split_id += 1


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