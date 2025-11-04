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

    race = memory.race()
    if not race:
        logging.error(translate("No race data found"))
        return False

    try:
        # Важно: открываем без BOM и с табуляцией как разделитель
        base_name = os.path.splitext(destination)[0]
        with open(base_name + '.sfrx', 'w', encoding='utf-8', newline='') as f:

            _write_header(f, race)
  
            _write_days(f, race)
   
            _write_federations(f)
     
            _write_clubs(f)
      
            _write_groups(f, race)
     
            _write_teams(f, race)
   
            _write_courses(f, race)
   
            _write_controls(f, race)
     
            _write_competitors(f, race)
   
            _write_splits(f, race)
            
        logging.info(translate("Export completed successfully to {}").format(destination))
        return True
        
    except Exception as e:
        logging.error(translate("Export error: {}").format(str(e)))
        return False


def _write_header(f, race: Race):

    title = race.data.title or "Competition"
    location = race.data.location or ""

    organizer = ""
    if hasattr(race.data, 'organizer') and race.data.organizer:
        organizer = race.data.organizer
    elif hasattr(race.data, 'organization') and race.data.organization:
        organizer = race.data.organization
    
    days = 1
   
    race_type = "Индивидуальные"
    if race.data.race_type and hasattr(race.data.race_type, 'value'):
        if race.data.race_type.value == "relay":
            race_type = "Эстафета"

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

    federation_fields = [
        "h0", 
        "Региональная ОО ФСО"
    ]
    f.write("\t".join(federation_fields) + "\n")


def _write_clubs(f):

    club_fields = [
        "f0",
        "Экстрим парк"
    ]
    f.write("\t".join(club_fields) + "\n")


def _write_groups(f, race: Race):

    for i, group in enumerate(race.groups):

        group_id_str = str(i).zfill(5)
        group_name = group.name or f"Group_{i}"
        
        course_index = "0"
        if group.course and group.course in race.courses:
            course_index = str(race.courses.index(group.course))
        
        group_fields = [
            f"g{group_id_str}",
            group_name,
            "-1", # входит в группу   -1 - не входит
            "0", "0",
            "",  # название соревнований для грамот
            "150",  # стартовый взнос
            course_index,
            "0", "0", "0",
            "5400000",  # контрольное время (90 минут)
            "0",
            ""  # пустое поле в конце
        ]
        f.write("\t".join(group_fields) + "\n")


def _write_teams(f, race: Race):

    for i, org in enumerate(race.organizations):

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

    for i, course in enumerate(race.courses):

        course_id_str = str(i).zfill(5)
        course_name = course.name or f"Course_{i}"

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
 
        course_fields.extend(control_pairs)
        
        f.write("\t".join(course_fields) + "\n")


def _write_controls(f, race: Race):
  
    control_codes = set()
    for course in race.courses:
        for control in course.controls:
            code_str = str(control.code)
            if code_str.isdigit() and code_str not in ['240', '241', '242']:
                control_codes.add(int(code_str))
    
    for i, code in enumerate(sorted(control_codes)):
   
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

    for i, person in enumerate(race.persons):

        person_id_str = str(i).zfill(5)

        group_id = "0"
        if person.group:
            for idx, group in enumerate(race.groups):
                if group == person.group:
                    group_id = str(idx)
                    break

        team_id = "0"
        if person.organization:
            for idx, org in enumerate(race.organizations):
                if org == person.organization:
                    team_id = str(idx)
                    break
 
        year = ""
        if person.year:
            year = str(person.year)
        elif person.birth_date:
            year = person.birth_date.strftime("%Y")
        
        birthday = person.birth_date.strftime("%d.%m.%Y") if person.birth_date else ""

        qual_id = sportorg_qual_to_sfr(person.qual) if person.qual else "0"
  
        result = race.find_person_result(person)
 
        start_time = ""
        if result and result.start_time:
            start_time = _format_time(result.start_time)
        elif person.start_time:
            start_time = _format_time(person.start_time)
 
        finish_time = ""
        if result and result.finish_time:
            finish_time = _format_time(result.finish_time)
   
        result_status = ""
        result_time = ""
        if result:
            if result.status == ResultStatus.OK:
                if result.finish_time and result.start_time:
                    result_time = _calculate_result_time(result.start_time, result.finish_time)
                elif result.finish_time:
                    result_time = _format_time(result.finish_time)
            elif result.status == ResultStatus.DISQUALIFIED:
                result_status = "cнят"  # с английской c
            elif result.status == ResultStatus.OVERTIME:
                result_status = "cнят (к/в)"
            elif result.status == ResultStatus.DID_NOT_FINISH:
                result_status = "cнят"
            elif result.status == ResultStatus.DID_NOT_START:
                result_status = "н/с"
            elif result.status == ResultStatus.MISSING_PUNCH:
                result_status = "cнят"
            elif result.status == ResultStatus.REJECTED:
                result_status = "cнят"
        else:
   
            if person.start_time:

                result_status = "cнят"
            else:

                result_status = "н/с"

        surname = person.surname or ""
        first_name = person.name or ""
        
        competitor_fields = [
            f"c{person_id_str}",
            str(person.bib or "0"),
            group_id,
            surname,
            first_name,
            team_id,
            birthday,
            qual_id,
            person.comment or "",
            "0",  # аренда карты
            "0",  # стартовый взнос
            "0",  # оплачено
            "0",  # дата оплаты
            start_time,      # абсолютное время старта
            finish_time,     # абсолютное время финиша
            "0",  # бонусное
            result_time or result_status,  # относительное время результата
            "0", 
            "0", 
            "0"  # массив из 7 полей (должен повторяться в многодневке - to do)
        ]
        f.write("\t".join(competitor_fields) + "\n")


def _write_splits(f, race: Race):

    split_id = 0
    
    for person in race.persons:
        result = race.find_person_result(person)
        if not result or not result.splits:
            continue
  
        course_index = "0"
        course = None
        if person.group and person.group.course:
            if person.group.course in race.courses:
                course_index = str(race.courses.index(person.group.course))
                course = person.group.course
    
        expected_codes = []
        if course and course.controls:
            for control in course.controls:
                code_str = str(control.code)
                if code_str not in ['240', '241', '242']:
                    expected_codes.append(code_str)
 
        valid_splits = [s for s in result.splits if s.time and s.code]
        sorted_splits = sorted(valid_splits, key=lambda x: x.time)
        
        if not sorted_splits:
            continue
            
        split_data = []
  
        current_position = 0

        for split in valid_splits:
            code_str = str(split.code)
            time_str = _format_time(split.time)
  
            if code_str in ['240', '241', '242']:
                order = "0"
                split_data.extend([code_str, order, time_str])
            else:

                found_position = -1
                for i in range(current_position, len(expected_codes)):
                    if code_str == expected_codes[i]:
                        found_position = i
                        break
                
                if found_position >= current_position:
  
                    order = str(found_position + 1)
                    current_position = found_position + 1
                else:

                    order = "0"
                
                split_data.extend([code_str, order, time_str])

        has_finish = any(str(split.code) == '240' for split in sorted_splits)
        if not has_finish and result and result.finish_time:
            finish_time_str = _format_time(result.finish_time)
            split_data.extend(["240", "0", finish_time_str])
 
        if split_data:
            split_id_str = str(split_id).zfill(5)
            split_fields = [
                f"s{split_id_str}",
                str(person.bib or "0"),
                course_index,  # номер дистанции
                "0",  # пустое поле
                "1",
                "128" # ?
            ]
            split_fields.extend(split_data)
            f.write("\t".join(split_fields) + "\n")
            split_id += 1

def _format_time(dt):

    if not dt:
        return ""
    
    try:

        if hasattr(dt, 'strftime'):
            return dt.strftime("%H:%M:%S")

        elif hasattr(dt, 'hour') and hasattr(dt, 'minute') and hasattr(dt, 'second'):
            return f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"

        elif hasattr(dt, 'hour') or hasattr(dt, 'minute'):
            hour = getattr(dt, 'hour', 0)
            minute = getattr(dt, 'minute', 0)
            second = getattr(dt, 'second', 0)

            if second == 0:
                second = getattr(dt, 'sec', 0)
            return f"{hour:02d}:{minute:02d}:{second:02d}"
        

        elif hasattr(dt, 'to_time') and callable(dt.to_time):
            time_obj = dt.to_time()
            if hasattr(time_obj, 'hour'):
                return f"{time_obj.hour:02d}:{time_obj.minute:02d}:{time_obj.second:02d}"

        elif isinstance(dt, str):

            if dt.count(':') == 2:
                return dt

            elif dt.count(':') == 1:
                return dt + ":00"
            return dt
            
    except Exception as e:
        logging.debug(f"Time formatting error for {type(dt)}: {e}")
    
    return ""

def _convert_to_datetime(time_obj):

    if not time_obj:
        return None
    
    try:
 
        if hasattr(time_obj, 'strftime') and hasattr(time_obj, 'date'):
            return time_obj

        elif hasattr(time_obj, 'hour') and hasattr(time_obj, 'minute') and hasattr(time_obj, 'second'):
            return datetime.combine(datetime.today().date(), 
                                  time(hour=time_obj.hour, minute=time_obj.minute, second=time_obj.second))

        elif hasattr(time_obj, 'to_datetime'):
            return time_obj.to_datetime()
    
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

    try:

        start_dt = _convert_to_datetime(start_time)
        finish_dt = _convert_to_datetime(finish_time)
        
        if start_dt and finish_dt:

            if finish_dt < start_dt:

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

    if not qual:
        return "0"
    
    qual_value = qual.value if hasattr(qual, 'value') else int(qual)
    
    return {
        0: "0",   # No qualification
        1: "3",   # МСМК - звание?
        2: "2",   # МС
        3: "1",   # КМС
        4: "6",   # I
        5: "5",   # II
        6: "4",   # III
        7: "7",   # Iю
        8: "8",   # IIю
        9: "9",   # IIIю
    }.get(qual_value, "0")