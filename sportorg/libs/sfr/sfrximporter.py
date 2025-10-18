import logging

from sportorg.language import translate
from sportorg.libs.sfr import sfrxparser
from sportorg.models import memory
from sportorg.models.memory import (
    Qualification,
    race,
    ResultManual,
    ResultStatus,
    Split,
    SystemType,
    Person,
)
from sportorg.utils.time import hhmmss_to_time, ddmmyyyy_to_time


def import_sfrx(source: str):
    sfr_csv = sfrxparser.parse(source)
    obj = memory.race()

    old_lengths = obj.get_lengths()

    settings = sfr_csv.settings
    race_type = settings["race_type"]

    obj.data.race_type = race_type
    obj.data.title = settings["title"]
    obj.data.location = settings["location"]

    for course in iter(sfr_csv.dists.values()):
        name = course["name"]
        bib = convert_bib(course["bib"])
        if bib != 0:
            name = str(bib)
        if name not in race().course_index_name:
            c = memory.create(
                memory.Course,
                bib=bib,
                name=name,
                length=int(course["length"]),
                climb=int(course["climb"]),
            )
            controls = []
            for order, control in enumerate(course["controls"]):
                if str(control["code"]).isdecimal():  # don't use start and finish
                    controls.append(
                        memory.create(
                            memory.CourseControl,
                            code=control["code"],
                            order=order,
                            length=int(control["length"]),
                        )
                    )
            c.controls = controls
            memory.race().courses.append(c)

    for group_val in iter(sfr_csv.groups.values()):
        group_name = group_val["name"]
        group = memory.find(obj.groups, name=group_name)
        if group is None:
            group = memory.Group()
            group.name = group_name
            group.long_name = group_name
            obj.groups.append(group)
        if group_val["course"] != -1:
            course = sfr_csv.dists[str(group_val["course"])]
            course = memory.find(memory.race().courses, name=course["name"])
            group.course = course

        group.race_type = race_type

    for team_name in iter(sfr_csv.teams.values()):
        org = memory.find(obj.organizations, name=team_name)
        if org is None:
            org = memory.Organization()
            org.name = team_name
            obj.organizations.append(org)

    for person_dict in sfr_csv.data:
        person = memory.Person()
        person.name = person_dict["name"]
        person.surname = person_dict["surname"]
        person.middle_name = person_dict["middle_name"]

        bib = convert_bib(str(person_dict["bib"]))

        person.set_bib(bib)
        person.set_year(person_dict["year"])
        if len(person_dict["birthday"]):
            person.birth_date = ddmmyyyy_to_time(person_dict["birthday"])
        group = person_dict["group_id"]

        if int(group) >= 0:
            person.group = memory.find(obj.groups, name=sfr_csv.groups[group]["name"])

        team = person_dict["team_id"]
        if int(team) >= 0:
            person.organization = memory.find(
                obj.organizations, name=sfr_csv.teams[team]
            )

        if person_dict["qual_id"] and person_dict["qual_id"].isdigit():
            qual_id = sfr_qual_to_sportorg(person_dict["qual_id"])
        else:
            qual_id = 0

        person.qual = Qualification(qual_id)
        person.comment = person_dict["comment"]
        set_property(person, "Finish", person_dict["finish"])
        set_property(person, "Result", person_dict["result"])
        set_property(person, "Credit", person_dict["credit"])
        set_property(person, "Start", person_dict["start"])

        obj.persons.append(person)

        result_person = race().find_person_result(person)
        if result_person:
            result_person.system_type = SystemType.SFR

    for split_csv in sfr_csv.splits:
        bib = convert_bib(split_csv["bib"])
        person = race().find_person_by_bib(bib)
        if person is None:
            continue
        result_person = race().find_person_result(person)
        if result_person is None:
            continue

        splits = []
        for split_csv_value in split_csv["split"]:
            split = Split()

            code = split_csv_value[0]
            if code == "240" or code == "241":
                continue

            split.code = code

            split.time = hhmmss_to_time(split_csv_value[1])
            splits.append(split)
        result_person.splits = splits

    new_lengths = obj.get_lengths()

    logging.info(translate("Import result"))
    logging.info("{}: {}".format(translate("Persons"), new_lengths[0] - old_lengths[0]))
    logging.info("{}: {}".format(translate("Groups"), new_lengths[2] - old_lengths[2]))
    logging.info("{}: {}".format(translate("Teams"), new_lengths[4] - old_lengths[4]))

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


def convert_bib(bib: str) -> int:
    if not bib.isdigit():
        return 0

    if int(bib) < 10000:
        return int(bib)
    else:
        return int(bib[0] + str(int(bib[1:])))


def sfr_qual_to_sportorg(value: str) -> int:
    return {
        "": 0,
        "0": 0,
        "1": 3,
        "2": 2,
        "3": 1,
        "4": 6,
        "5": 5,
        "6": 4,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 8,
    }[value]


def set_property(person: Person, key: str, value: str) -> None:
    if value == "":
        return

    if key == "Start":
        result = race().find_person_result(person)
        if result:
            result.start_time = hhmmss_to_time(value)
            person.start_time = hhmmss_to_time(value)
        else:
            person.start_time = hhmmss_to_time(value)
    elif key == "Finish":
        result = race().find_person_result(person)
        if not result:
            result = race().new_result(ResultManual)
            result.person = person
            result.bib = person.bib
            race().add_new_result(result)
        result.finish_time = hhmmss_to_time(value)
    elif key == "Credit":
        result = race().find_person_result(person)
        if result:
            result.credit_time = hhmmss_to_time(value)
    elif key == "Result":
        result_sfr = value
        if result_sfr and len(result_sfr.split(":")) != 3:
            result_person = race().find_person_result(person)
            if result_person is None:
                result_person = race().new_result(ResultManual)
                result_person.person = person
                result_person.bib = person.bib
                race().add_new_result(result_person)
            if result_sfr == "cнят":
                result_person.status = ResultStatus.DISQUALIFIED
            if result_sfr == "cнят (запр.)":
                result_person.status = ResultStatus.DISQUALIFIED
            if result_sfr == "cнят (к/в)":
                result_person.status = ResultStatus.OVERTIME
            if result_sfr == "н/с":
                result_person.status = ResultStatus.DID_NOT_START
