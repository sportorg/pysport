import copy
import datetime
import logging
from datetime import time

import dateutil.parser

from sportorg.common.otime import OTime
from sportorg.language import translate
from sportorg.libs.iof.generator import (
    generate_competitor_list,
    generate_entry_list,
    generate_result_list,
    generate_start_list,
)
from sportorg.libs.iof.parser import parse
from sportorg.models.memory import (
    Course,
    CourseControl,
    Group,
    Organization,
    Person,
    Qualification,
    ResultSportident,
    ResultStatus,
    Split,
    create,
    find,
    race,
)
from sportorg.utils.time import hhmmss_to_time, time_iof_to_otime, yyyymmdd_to_date


def export_result_list(file, *, creator: str, all_splits: bool = False) -> None:
    obj = race()

    result_list = generate_result_list(obj, creator=creator, all_splits=all_splits)

    result_list.write(open(file, "wb"), xml_declaration=True, encoding="UTF-8")


def export_entry_list(file, *, creator: str) -> None:
    obj = race()

    entry_list = generate_entry_list(obj, creator=creator)

    entry_list.write(open(file, "wb"), xml_declaration=True, encoding="UTF-8")


def export_start_list(file, *, creator: str) -> None:
    obj = race()

    start_list = generate_start_list(obj, creator=creator)

    start_list.write(open(file, "wb"), xml_declaration=True, encoding="UTF-8")


def export_competitor_list(file, *, creator: str) -> None:
    obj = race()

    start_list = generate_competitor_list(obj, creator=creator)

    start_list.write(open(file, "wb"), xml_declaration=True, encoding="UTF-8")


def import_from_iof(file) -> None:
    results = parse(file)
    if not len(results):
        return

    for result in results:
        if result.name == "EntryList":
            import_from_entry_list(result.data)
        elif result.name == "CourseData":
            import_from_course_data(result.data)
        elif result.name == "VariationData":
            import_from_variation_data(result.data)
        elif result.name == "ResultList":
            import_from_result_list(result.data)
        elif result.name == "StartList":
            import_from_entry_list(result.data)
        elif result.name == "Event":
            import_from_event_data(result.data)


def import_from_course_data(courses) -> None:
    obj = race()
    for course in courses:
        if "name" in course:
            if find(obj.courses, name=course["name"]) is None:
                c = create(
                    Course,
                    name=course["name"],
                    length=course["length"],
                    climb=course["climb"],
                )
                controls = []
                i = 1
                for control in course["controls"]:
                    if control["type"] == "Control":
                        controls.append(
                            create(
                                CourseControl,
                                code=control["control"],
                                order=i,
                                length=control["leg_length"],
                            )
                        )
                        i += 1
                c.controls = controls
                obj.courses.append(c)


def import_from_variation_data(teams) -> None:
    obj = race()
    for team in teams:
        for leg in team["legs"]:
            leg_number = leg["leg_number"]
            course_name = leg["course_name"]
            course = find(obj.courses, name=course_name)
            if course:
                new_course = Course()
                new_course.name = str(team["bib_number"]) + "." + str(leg_number)
                new_course.length = course.length
                new_course.controls = copy.deepcopy(course.controls)
                obj.courses.append(new_course)


def create_person(person_entry):
    obj = race()

    person = Person()

    name = person_entry["group"]["name"]
    if (
        "short_name" in person_entry["group"]
        and len(person_entry["group"]["short_name"]) > 0
    ):
        name = person_entry["group"]["short_name"]
    group = find(obj.groups, name=name)
    if group is None:
        group = Group()
        group.long_name = person_entry["group"]["name"]
        if (
            "short_name" in person_entry["group"]
            and len(person_entry["group"]["short_name"]) > 0
        ):
            group.name = person_entry["group"]["short_name"]
        else:
            group.name = group.long_name
        obj.groups.append(group)
    person.group = group

    if person_entry["organization"]:
        org = find(obj.organizations, name=person_entry["organization"]["name"])
        if org is None:
            org = Organization()
            org.name = person_entry["organization"]["name"]
            if "role_person" in person_entry["organization"]:
                org.contact = person_entry["organization"]["role_person"]
            obj.organizations.append(org)
        person.organization = org

    person.surname = person_entry["person"]["family"]
    person.name = person_entry["person"]["given"]
    person.extract_middle_name()

    if "id" in person_entry["person"]:
        person.world_code = str(person_entry["person"]["id"])
    if "birth_date" in person_entry["person"]:
        person.birth_date = (
            dateutil.parser.parse(person_entry["person"]["birth_date"]).date()
            if person_entry["person"]["birth_date"]
            else 0
        )
    if "race_numbers" in person_entry and len(person_entry["race_numbers"]):
        person.comment = "C:" + "".join(person_entry["race_numbers"])
    if "control_card" in person_entry and person_entry["control_card"]:
        person.set_card_number(int(person_entry["control_card"]))
    if "bib" in person_entry["person"] and person_entry["person"]["bib"]:
        person.set_bib(int(person_entry["person"]["bib"]))
    elif (
        "bib" in person_entry["person"]["extensions"]
        and person_entry["person"]["extensions"]["bib"]
    ):
        person.set_bib(int(person_entry["person"]["extensions"]["bib"]))
    if (
        "qual" in person_entry["person"]["extensions"]
        and person_entry["person"]["extensions"]["qual"]
    ):
        person.qual = Qualification.get_qual_by_name(
            person_entry["person"]["extensions"]["qual"]
        )
    if "start" in person_entry["person"] and person_entry["person"]["start"]:
        person.start_time = time_iof_to_otime(person_entry["person"]["start"])

    obj.persons.append(person)
    return person


def import_from_entry_list(entries) -> None:
    obj = race()
    for person_entry in entries:
        create_person(person_entry)

    persons_dupl_cards = obj.get_duplicate_card_numbers()
    persons_dupl_names = obj.get_duplicate_names()

    if len(persons_dupl_cards):
        logging.info(
            "{}".format(translate("Duplicate card numbers (card numbers are reset)"))
        )
        for person in sorted(persons_dupl_cards, key=lambda x: x.card_number):
            logging.info(
                "{} {} {} {}".format(
                    person.full_name,
                    person.group.name if person.group else "",
                    person.organization.name if person.organization else "",
                    person.card_number,
                )
            )
            person.set_card_number(0)
    if len(persons_dupl_names):
        logging.info("{}".format(translate("Duplicate names")))
        for person in sorted(persons_dupl_names, key=lambda x: x.full_name):
            logging.info(
                "{} {} {} {}".format(
                    person.full_name,
                    person.get_year(),
                    person.group.name if person.group else "",
                    person.organization.name if person.organization else "",
                )
            )


def import_from_result_list(results) -> None:
    obj = race()

    for person_obj in results:
        result_obj = person_obj["result"]

        person = create_person(person_obj)

        bib = 0
        if "bib" in result_obj and str(result_obj["bib"]).strip():
            bib = int(result_obj["bib"])
        start = OTime()
        if "start_time" in result_obj:
            start = time_iof_to_otime(result_obj["start_time"])
        finish = OTime()
        if "finish_time" in result_obj:
            finish = time_iof_to_otime(result_obj["finish_time"])
        card = 0
        if "control_card" in result_obj and str(result_obj["control_card"]).strip():
            card = int(result_obj["control_card"])

        status = ResultStatus.OK

        if "status" in result_obj:
            status_text = result_obj["status"]
            if status_text == "DidNotStart":
                status = ResultStatus.DID_NOT_START
            elif status_text == "DidNotFinish":
                status = ResultStatus.DID_NOT_FINISH
            elif status_text == "OverTime":
                status = ResultStatus.OVERTIME
            elif status_text == "MissingPunch":
                status = ResultStatus.MISSING_PUNCH
            elif status_text == "Disqualified":
                status = ResultStatus.DISQUALIFIED

        new_result = ResultSportident()
        new_result.status = status

        if bib > 0:
            new_result.bib = bib
        new_result.start_time = start
        new_result.finish_time = finish
        if card > 0:
            new_result.card_number = card
        if person.card_number == 0:
            person.set_card_number(new_result.card_number)

        person.set_bib(int(bib))
        person.start_time = start
        new_result.person = person

        if "splits" in result_obj:
            for cur_split in result_obj["splits"]:
                new_split = Split()
                new_split.code = cur_split["control_code"]
                split_time = cur_split["time"]
                time_ms = int(float(str(split_time).replace(",", ".")) * 1000)
                new_time = start + OTime(msec=time_ms)
                new_split.time = new_time
                new_result.splits.append(new_split)

        obj.results.append(new_result)


def import_from_event_data(data) -> None:
    """Get info about event from Event and Event-Race[0] elements"""

    obj = race()

    if "name" in data:
        new_name = data["name"]
        if (
            new_name
            and len(new_name) > 0
            and new_name != "Event"
            and new_name.find("Example") < 0
        ):
            obj.data.title = data["name"]

    if "start_date" in data:
        date_val = yyyymmdd_to_date(data["start_date"], "-")
        obj.data.start_datetime = datetime.datetime.combine(date_val, time())

    if "races" in data and len(data["races"]) > 0:
        race_data = data["races"][0]
        if "name" in race_data:
            obj.data.description = obj.data.description + "\n" + race_data["name"]
        if "date" in race_data and "time" in race_data:
            date_val = yyyymmdd_to_date(race_data["date"], "-")
            otime_val = hhmmss_to_time(str(race_data["time"]).split("+")[0])
            time_val = time(
                hour=otime_val.hour, minute=otime_val.minute, second=otime_val.sec
            )
            obj.data.start_datetime = datetime.datetime.combine(date_val, time_val)
