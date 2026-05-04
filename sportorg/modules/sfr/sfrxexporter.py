import os
import logging
from datetime import datetime, time, timedelta
from sportorg import config
from sportorg.language import translate
from sportorg.models import memory
from sportorg.models.memory import (
    Qualification,
    Race,
    RaceType,
    ResultStatus,
)


def export_sfr_data(destination: str, export_type="file"):
    race = memory.race()
    if not race:
        logging.error(translate("No race data found"))
        return False
    if export_type == "file":
        return export_sfrx(destination)
    return False


def export_sfrx(destination: str):
    race = memory.race()
    if not race:
        logging.error(translate("No race data found"))
        return False
    try:
        base_name = os.path.splitext(destination)[0]
        with open(base_name + ".sfrx", "w", encoding="utf-8", newline="") as f:
            _write_header(f, race)
            _write_days(f, race)
            _write_descriptions(f, race)
            _write_clubs(f, race)
            _write_groups(f, race)
            _write_teams(f, race)
            _write_courses(f, race)
            _write_controls(f, race)
            _write_competitors(f, race)
            _write_splits(f, race)

        logging.info(
            translate("Export completed successfully to {}").format(base_name + ".sfrx")
        )
        return True

    except Exception as e:
        logging.error(translate("Export error: {}").format(str(e)))
        return False


def _write_header(f, race: Race):
    title = race.data.title or "Соревнования"
    location = race.data.location or "Место"
    name_style = "Фамилия и имя заглавными"
    punch_bib_style = "Номер команды и этап (последняя цифра)"
    days = 1
    race_type = "Индивидуальные"
    if race.data.race_type == RaceType.RELAY:
        race_type = "Эстафета"
    write_from = "SportOrg Export " + config.VERSION
    chief_referee = race.data.chief_referee or ""
    chief_secretary = race.data.secretary or ""
    header_fields = [
        "SFRx_v2404",
        title,
        location,
        str(days),
        "",
        chief_referee,
        chief_secretary,
        race_type,
        name_style,
        punch_bib_style,
        "",
        "",
        "",
        "",
        write_from,
    ]
    f.write("\t".join(header_fields) + "\n")


def _write_days(f, race: Race):
    first_url = ""
    url_list = race.get_setting("live_urls", [])
    if url_list and isinstance(url_list, list) and len(url_list) > 0:
        first_url = url_list[0]
    w_url = first_url or ""

    start_date = race.data.start_datetime or datetime.now()
    date_str = start_date.strftime("%d.%m.%Y")

    discipline = "Кросс - спринт"
    if race.data.race_type == RaceType.RELAY:
        discipline = "Эстафета"

    day_fields = ["p1", discipline, date_str, w_url]
    f.write("\t".join(day_fields) + "\n")


def _write_descriptions(f, race: Race):
    description_field = race.data.description or ""
    lines = [line.strip() for line in description_field.split("<br>")]
    for i, line in enumerate(lines):
        f.write(f"h{i}\t{line}\n")


def _write_clubs(f, race: Race):
    description_field = race.data.description or ""
    lines = [line.strip() for line in description_field.split("<br>")]
    for i, line in enumerate(lines):
        f.write(f"f{i}\t{line}\n")


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
            "-1",
            "0",
            "0",
            "",
            "0",
            course_index,
            "0",
            "0",
            "0",
            "5400000",
            "0",
            "",
        ]
        f.write("\t".join(group_fields) + "\n")


def _write_teams(f, race: Race):
    for i, org in enumerate(race.organizations):
        team_id_str = str(i).zfill(5)
        team_name = org.name or f"Team_{i}"

        team_fields = [f"t{team_id_str}", team_name, "-1", "", "", "", "0", ""]
        f.write("\t".join(team_fields) + "\n")


def _write_courses(f, race: Race):
    for i, course in enumerate(race.courses):
        course_id_str = str(i).zfill(5)
        course_name = course.name or f"Course_{i}"

        control_pairs = []
        if course.controls:
            for control in course.controls:
                code_str = str(control.code)
                if code_str.isdigit() and code_str not in ["240", "241", "242"]:
                    control_pairs.extend([code_str, str(control.length or "0")])

        course_fields = [
            f"d{course_id_str}",
            course_name,
            str(course.bib or "0"),
            "1",
            "0",
            "0",
            str(course.length or "0"),
            str(course.climb or "0"),
            str(len(control_pairs) // 2),
        ]

        course_fields.extend(control_pairs)

        f.write("\t".join(course_fields) + "\n")


def _write_controls(f, race: Race):
    control_codes = set()
    for course in race.courses:
        for control in course.controls:
            code_str = str(control.code)
            if code_str.isdigit() and code_str not in ["240", "241", "242"]:
                control_codes.add(int(code_str))

    for i, code in enumerate(sorted(control_codes)):
        control_id_str = str(i).zfill(5)

        control_fields = [
            f"k{control_id_str}",
            str(code),
            str(code),
            "0",
            "0",
            "0",
            "-1",
            "",
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

        birthday = person.birth_date.strftime("%d.%m.%Y") if person.birth_date else ""

        qual_id = sportorg_qual_to_sfr(person.qual) if person.qual else "0"

        result = race.find_person_result(person)

        start_value = _get_start_time(result, person)
        finish_value = _get_finish_time(result)

        start_time = _format_time(start_value)
        finish_time = _format_time(finish_value)
        result_value = _get_result_value(result, start_value, finish_value, person)

        surname = person.surname or ""
        first_name = " ".join(
            value for value in [person.name or "", person.middle_name or ""] if value
        )

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
            "0",
            "0",
            "0",
            "0",
            start_time,
            finish_time,
            "0",
            result_value,
            "0",
            "0",
            "0",
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
                if code_str not in ["240", "241", "242"]:
                    expected_codes.append(code_str)

        valid_splits = [s for s in result.splits if s.time and s.code]
        sorted_splits = sorted(valid_splits, key=lambda x: x.time)

        if not sorted_splits:
            continue

        split_data = []

        current_position = 0

        for split in sorted_splits:
            code_str = str(split.code)
            time_str = _format_time(split.time)

            if code_str in ["240", "241", "242"]:
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

        has_finish = any(str(split.code) == "240" for split in sorted_splits)
        if not has_finish and result and result.finish_time:
            finish_time_str = _format_time(result.finish_time)
            split_data.extend(["240", "0", finish_time_str])

        if split_data:
            split_id_str = str(split_id).zfill(5)
            split_fields = [
                f"s{split_id_str}",
                str(person.bib or "0"),
                course_index,
                "0",
                "1",
                "128",
            ]
            split_fields.extend(split_data)
            f.write("\t".join(split_fields) + "\n")
            split_id += 1


def _get_start_time(result, person):
    if result:
        get_start_time = getattr(result, "get_start_time", None)
        if callable(get_start_time):
            start_time = get_start_time()
            if start_time:
                return start_time

        start_time = getattr(result, "start_time", None)
        if start_time:
            return start_time

    return getattr(person, "start_time", None)


def _get_finish_time(result):
    if not result:
        return None

    finish_time = getattr(result, "finish_time", None)
    if finish_time:
        return finish_time

    get_finish_time = getattr(result, "get_finish_time", None)
    if callable(get_finish_time):
        return get_finish_time()

    return None


def _get_result_value(result, start_time, finish_time, person):
    if not result:
        return "cнят" if getattr(person, "start_time", None) else "н/с"

    if _is_status_ok(getattr(result, "status", None)):
        get_result_otime = getattr(result, "get_result_otime", None)
        if callable(get_result_otime):
            try:
                result_time = get_result_otime()
                if result_time:
                    formatted_time = _format_time(result_time)
                    if formatted_time:
                        return formatted_time
            except Exception as e:
                logging.debug(f"Result time formatting error: {e}")

        if start_time and finish_time:
            return _calculate_result_time(start_time, finish_time)
        if finish_time:
            return _format_time(finish_time)
        return ""

    return _format_status(getattr(result, "status", None))


def _is_status_ok(status):
    return status in (ResultStatus.OK, ResultStatus.RESTORED)


def _format_status(status):
    if status == ResultStatus.OVERTIME:
        return "cнят (к/в)"
    if status == ResultStatus.DID_NOT_START:
        return "н/с"
    return "cнят"


def _format_time(dt):
    if dt is None:
        return ""

    try:
        to_str = getattr(dt, "to_str", None)
        if callable(to_str):
            return to_str()

        if isinstance(dt, str):
            if dt.count(":") == 1:
                return dt + ":00"
            return dt

        if hasattr(dt, "strftime"):
            return dt.strftime("%H:%M:%S")

        hour = _get_time_part(dt, "hour")
        minute = _get_time_part(dt, "minute")
        second = _get_time_part(dt, "second", None)
        if second is None:
            second = _get_time_part(dt, "sec")

        if hour is not None or minute is not None:
            return f"{hour or 0:02d}:{minute or 0:02d}:{second or 0:02d}"

        if hasattr(dt, "to_time") and callable(dt.to_time):
            time_obj = dt.to_time()
            if hasattr(time_obj, "hour"):
                return (
                    f"{time_obj.hour:02d}:{time_obj.minute:02d}:{time_obj.second:02d}"
                )

    except Exception as e:
        logging.debug(f"Time formatting error for {type(dt)}: {e}")
    return ""


def _get_time_part(obj, name, default=0):
    value = getattr(obj, name, default)
    if callable(value):
        value = value()
    return value


def _convert_to_datetime(time_obj):
    if time_obj is None:
        return None

    try:
        if isinstance(time_obj, datetime):
            return time_obj

        if isinstance(time_obj, time):
            return datetime.combine(datetime.today().date(), time_obj)

        to_time = getattr(time_obj, "to_time", None)
        if callable(to_time):
            return datetime.combine(datetime.today().date(), to_time())

        if hasattr(time_obj, "to_datetime"):
            return time_obj.to_datetime()

        hour = _get_time_part(time_obj, "hour")
        minute = _get_time_part(time_obj, "minute")
        second = _get_time_part(time_obj, "second", None)
        if second is None:
            second = _get_time_part(time_obj, "sec")
        if hour is not None or minute is not None:
            return datetime.combine(
                datetime.today().date(),
                time(hour=hour or 0, minute=minute or 0, second=second or 0),
            )

    except Exception as e:
        logging.debug(f"Time conversion error: {e}")
    return None


def _calculate_result_time(start_time, finish_time):
    try:
        start_dt = _convert_to_datetime(start_time)
        finish_dt = _convert_to_datetime(finish_time)

        if start_dt and finish_dt:
            if finish_dt < start_dt:
                finish_dt += timedelta(days=1)

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

    qual_value = qual.value if hasattr(qual, "value") else int(qual)

    return {
        0: "0",
        1: "3",
        2: "2",
        3: "1",
        4: "6",
        5: "5",
        6: "4",
        7: "7",
        8: "8",
        9: "9",
    }.get(qual_value, "0")
