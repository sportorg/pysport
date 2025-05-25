import xml.etree.ElementTree as ET


class IOFParseResult:
    def __init__(self, name, data):
        self.name = name
        self.data = data


def parse(file):
    ns = {
        "iof": "http://www.orienteering.org/datastandard/3.0",
        "orgeo": "http://orgeo.ru/iof-xml-extensions/3.0",
    }
    tree = ET.parse(file)

    results = [
        IOFParseResult("EntryList", entry_list(tree, ns)),
        IOFParseResult("StartList", start_list(tree, ns)),
        IOFParseResult("CourseData", course_data(tree, ns)),
        IOFParseResult("ResultList", result_list(tree, ns)),
        IOFParseResult("Event", event(tree, ns)),
    ]

    return [result for result in results if result.data is not None]


def course_data(tree, ns):
    root = tree.getroot()
    if "CourseData" not in root.tag:
        return
    courses = []

    version = "0"
    if "iofVersion" in root.attrib:
        version = root.attrib["iofVersion"][0]
    elif root.find("IOFVersion") is not None:
        version = root.find("IOFVersion").attrib["version"][0]

    if version == "3":
        for course_el in root.find("iof:RaceCourseData", ns).findall("iof:Course", ns):
            course = {
                "name": course_el.find("iof:Name", ns).text,
                "length": int(course_el.find("iof:Length", ns).text),
                "climb": int(course_el.find("iof:Climb", ns).text)
                if course_el.find("iof:Climb", ns)
                else 0,
                "controls": [],
            }

            for course_control_el in course_el.findall("iof:CourseControl", ns):
                leg_length = 0
                if course_control_el.find("iof:LegLength", ns) is not None:
                    leg_length = int(course_control_el.find("iof:LegLength", ns).text)
                course["controls"].append(
                    {
                        "type": course_control_el.attrib[
                            "type"
                        ],  # Start, Control, Finish
                        "control": course_control_el.find("iof:Control", ns).text,
                        "leg_length": leg_length,
                    }
                )
            courses.append(course)

    elif version == "2":
        for course_el in root.findall("Course"):
            course_variation_el = course_el.find("CourseVariation")
            course = {
                "name": course_el.find("CourseName").text.strip(),
                "length": int(course_variation_el.find("CourseLength").text),
                "climb": (
                    int(course_variation_el.find("CourseClimb").text.strip())
                    if course_variation_el.find("CourseClimb").text.strip().isdigit()
                    else 0
                ),
                "controls": [],
            }

            for course_control_el in course_variation_el.findall("CourseControl"):
                leg_length = 0
                if course_control_el.find("LegLength") is not None:
                    leg_length = int(course_control_el.find("LegLength").text)
                course["controls"].append(
                    {
                        "type": "Control",
                        "control": course_control_el.find("ControlCode").text.strip(),
                        "leg_length": leg_length,
                    }
                )
            courses.append(course)

    return courses


def entry_list(tree, ns):
    root = tree.getroot()
    if "EntryList" not in root.tag:
        return
    groups = {}
    for group_el in root.findall("iof:Class", ns):
        group_id = group_el.find("iof:Id", ns).text
        groups[group_id] = {
            "id": group_id,
            "name": group_el.find("iof:Name", ns).text,
            "short_name": group_el.find("iof:ShortName", ns).text,
        }
    person_entries = []

    if root.find("iof:PersonEntry", ns):
        for person_entry_el in root.findall("iof:PersonEntry", ns):
            person_el = person_entry_el.find("iof:Person", ns)
            birth_date_el = person_el.find("iof:BirthDate", ns)
            id_el = person_el.find("iof:Id", ns)
            person = {
                "family": person_el.find("iof:Name", ns).find("iof:Family", ns).text,
                "given": person_el.find("iof:Name", ns).find("iof:Given", ns).text,
                "extensions": {},
            }
            if birth_date_el is not None:
                person["birth_date"] = birth_date_el.text
            if id_el is not None:
                person["id"] = id_el.text

            extensions_el = person_el.find("iof:Extensions", ns)
            if extensions_el:
                qual_el = extensions_el.find("orgeo:Qual", ns)
                if qual_el is not None:
                    person["extensions"]["qual"] = qual_el.text
                bib_el = extensions_el.find("orgeo:BibNumber", ns)
                if bib_el is not None:
                    person["extensions"]["bib"] = bib_el.text

            org_el = person_entry_el.find("iof:Organisation", ns)
            organization = None
            if org_el:
                organization = {
                    "id": org_el.find("iof:Id", ns).text,
                    "name": org_el.find("iof:Name", ns).text,
                }
                role = org_el.find("iof:Role", ns)
                if role:
                    role_person = role.find("iof:Person", ns)
                    organization["role_person"] = "{} {}".format(
                        role_person.find("iof:Name", ns).find("iof:Family", ns).text,
                        role_person.find("iof:Name", ns).find("iof:Given", ns).text,
                    )

            group_el = person_entry_el.find("iof:Class", ns)
            if group_el:
                group = {
                    "id": group_el.find("iof:Id", ns).text,
                    "name": group_el.find("iof:Name", ns).text,
                }
                groups[group["id"]] = {"id": group["id"], "name": group["name"]}

            control_card_el = person_entry_el.find("iof:ControlCard", ns)
            control_card = ""
            if control_card_el is not None:
                control_card = control_card_el.text

            race_numbers = []
            for race_num_el in person_entry_el.findall("iof:RaceNumber", ns):
                race_numbers.append(race_num_el.text)

            person_entries.append(
                {
                    "person": person,
                    "organization": organization,
                    "group": groups[group["id"]] if group["id"] in groups else group,
                    "control_card": control_card,
                    "race_numbers": race_numbers,
                }
            )
    elif root.find("iof:TeamEntry", ns):
        for team_entry_el in root.findall("iof:TeamEntry", ns):
            org_el = team_entry_el.find("iof:Organisation", ns)
            organization = None
            if org_el:
                organization = {
                    "id": org_el.find("iof:Id", ns).text,
                    "name": org_el.find("iof:Name", ns).text,
                }
                role = org_el.find("iof:Role", ns)
                if role:
                    role_person = role.find("iof:Person", ns)
                    organization["role_person"] = "{} {}".format(
                        role_person.find("iof:Name", ns).find("iof:Family", ns).text,
                        role_person.find("iof:Name", ns).find("iof:Given", ns).text,
                    )

            group_el = team_entry_el.find("iof:Class", ns)
            if group_el:
                group = {
                    "id": group_el.find("iof:Id", ns).text,
                    "name": group_el.find("iof:Name", ns).text,
                }
                groups[group["id"]] = {"id": group["id"], "name": group["name"]}

            race_numbers = []
            for race_num_el in team_entry_el.findall("iof:RaceNumber", ns):
                race_numbers.append(race_num_el.text)

            for team_entry_person_el in team_entry_el.findall(
                "iof:TeamEntryPerson", ns
            ):
                person_el = team_entry_person_el.find("iof:Person", ns)
                birth_date_el = person_el.find("iof:BirthDate", ns)
                id_el = person_el.find("iof:Id", ns)
                person = {
                    "family": person_el.find("iof:Name", ns)
                    .find("iof:Family", ns)
                    .text,
                    "given": person_el.find("iof:Name", ns).find("iof:Given", ns).text,
                    "extensions": {},
                }
                if birth_date_el is not None:
                    person["birth_date"] = birth_date_el.text
                if id_el is not None:
                    person["id"] = id_el.text

                control_card_el = team_entry_person_el.find("iof:ControlCard", ns)
                control_card = ""
                if control_card_el is not None:
                    control_card = control_card_el.text

                person_entries.append(
                    {
                        "person": person,
                        "organization": organization,
                        "group": (
                            groups[group["id"]] if group["id"] in groups else group
                        ),
                        "control_card": control_card,
                        "race_numbers": race_numbers,
                    }
                )
    return person_entries


def start_list(tree, ns):
    root = tree.getroot()
    if "StartList" not in root.tag:
        return

    groups = {}

    person_starts = []

    for class_start in root.findall("iof:ClassStart", ns):
        """Group of starts for class"""
        group_el = class_start.find("iof:Class", ns)
        group_id = group_el.find("iof:Id", ns).text
        groups[group_id] = {
            "id": group_id,
            "name": group_el.find("iof:Name", ns).text,
            "short_name": (
                group_el.find("iof:ShortName", ns).text
                if group_el.find("iof:ShortName", ns)
                else ""
            ),
        }

        if class_start.find("iof:PersonStart", ns):
            for person_start_el in class_start.findall("iof:PersonStart", ns):
                person_el = person_start_el.find("iof:Person", ns)
                birth_date_el = person_el.find("iof:BirthDate", ns)
                id_el = person_el.find("iof:Id", ns)
                person = {
                    "family": person_el.find("iof:Name", ns)
                    .find("iof:Family", ns)
                    .text,
                    "given": person_el.find("iof:Name", ns).find("iof:Given", ns).text,
                    "extensions": {},
                }
                if birth_date_el is not None:
                    person["birth_date"] = birth_date_el.text
                if id_el is not None:
                    person["id"] = id_el.text

                org_el = person_start_el.find("iof:Organisation", ns)
                organization = None
                if org_el:
                    organization = {"name": org_el.find("iof:Name", ns).text}
                    if org_el.find("iof:Id", ns):
                        organization["id"] = org_el.find("iof:Id", ns).text

                    role = org_el.find("iof:Role", ns)
                    if role:
                        role_person = role.find("iof:Person", ns)
                        organization["role_person"] = "{} {}".format(
                            role_person.find("iof:Name", ns)
                            .find("iof:Family", ns)
                            .text,
                            role_person.find("iof:Name", ns).find("iof:Given", ns).text,
                        )

                start_el = person_start_el.find("iof:Start", ns)
                bib_el = start_el.find("iof:BibNumber", ns)
                if bib_el is not None:
                    person["bib"] = bib_el.text
                control_card_el = start_el.find("iof:ControlCard", ns)
                start_time_el = start_el.find("iof:StartTime", ns)
                if start_time_el is not None:
                    person["start"] = start_time_el.text

                control_card = ""
                if control_card_el is not None:
                    control_card = control_card_el.text

                person_starts.append(
                    {
                        "person": person,
                        "organization": organization,
                        "group": groups[group_id],
                        "control_card": control_card,
                        "result": {},
                    }
                )

        elif class_start.find("iof:TeamStart", ns):
            for team_start_el in class_start.findall("iof:TeamStart", ns):
                bib_number = team_start_el.find("iof:BibNumber", ns).text
                for team_member_start_el in team_start_el.findall(
                    "iof:TeamMemberStart", ns
                ):
                    person_el = team_member_start_el.find("iof:Person", ns)

                    if not person_el:
                        # Person element is omitted, no competitor on 2nd and 3rd leg,
                        # but TeamMemberResult elements for these legs must be present anyway
                        continue

                    birth_date_el = person_el.find("iof:BirthDate", ns)
                    id_el = person_el.find("iof:Id", ns)
                    person = {
                        "family": person_el.find("iof:Name", ns)
                        .find("iof:Family", ns)
                        .text,
                        "given": person_el.find("iof:Name", ns)
                        .find("iof:Given", ns)
                        .text,
                        "extensions": {},
                    }
                    if birth_date_el is not None:
                        person["birth_date"] = birth_date_el.text
                    if id_el is not None:
                        person["id"] = id_el.text

                    org_el = team_member_start_el.find("iof:Organisation", ns)
                    organization = None
                    if org_el is not None:
                        organization = {"name": org_el.find("iof:Name", ns).text}
                        if org_el.find("iof:Id", ns) is not None:
                            organization["id"] = org_el.find("iof:Id", ns).text

                        role = org_el.find("iof:Role", ns)
                        if role is not None:
                            role_person = role.find("iof:Person", ns)
                            organization["role_person"] = "{} {}".format(
                                role_person.find("iof:Name", ns)
                                .find("iof:Family", ns)
                                .text,
                                role_person.find("iof:Name", ns)
                                .find("iof:Given", ns)
                                .text,
                            )

                    start_el = team_member_start_el.find("iof:Start", ns)
                    control_card_el = start_el.find("iof:ControlCard", ns)
                    start_time_el = start_el.find("iof:StartTime", ns)
                    if start_time_el is not None:
                        person["start"] = start_time_el.text

                    leg_el = start_el.find("iof:Leg", ns)
                    leg = leg_el.text
                    if leg and bib_number and leg.isdigit() and bib_number.isdigit():
                        final_bib = str(int(leg) * 1000 + int(bib_number))
                        person["bib"] = final_bib

                    control_card = ""
                    if control_card_el is not None:
                        control_card = control_card_el.text

                    person_starts.append(
                        {
                            "person": person,
                            "organization": organization,
                            "group": groups[group_id],
                            "control_card": control_card,
                            "result": {},
                        }
                    )

    return person_starts


def result_list(tree, ns):
    root = tree.getroot()
    if "ResultList" not in root.tag:
        return
    groups = {}

    person_results = []

    for class_result in root.findall("iof:ClassResult", ns):
        """Group of results for class"""
        group_el = class_result.find("iof:Class", ns)
        group_id = group_el.find("iof:Id", ns).text
        groups[group_id] = {
            "id": group_id,
            "name": group_el.find("iof:Name", ns).text,
            "short_name": (
                group_el.find("iof:ShortName", ns).text
                if group_el.find("iof:ShortName", ns)
                else ""
            ),
        }

        if class_result.find("iof:PersonResult", ns):
            for person_result_el in class_result.findall("iof:PersonResult", ns):
                person_el = person_result_el.find("iof:Person", ns)
                birth_date_el = person_el.find("iof:BirthDate", ns)
                id_el = person_el.find("iof:Id", ns)
                person = {
                    "family": person_el.find("iof:Name", ns)
                    .find("iof:Family", ns)
                    .text,
                    "given": person_el.find("iof:Name", ns).find("iof:Given", ns).text,
                    "extensions": {},
                }
                if birth_date_el is not None:
                    person["birth_date"] = birth_date_el.text
                if id_el is not None:
                    person["id"] = id_el.text

                org_el = person_result_el.find("iof:Organisation", ns)
                organization = None
                if org_el:
                    organization = {"name": org_el.find("iof:Name", ns).text}
                    if org_el.find("iof:Id", ns):
                        organization["id"] = org_el.find("iof:Id", ns).text

                    role = org_el.find("iof:Role", ns)
                    if role:
                        role_person = role.find("iof:Person", ns)
                        organization["role_person"] = "{} {}".format(
                            role_person.find("iof:Name", ns)
                            .find("iof:Family", ns)
                            .text,
                            role_person.find("iof:Name", ns).find("iof:Given", ns).text,
                        )

                result_el = person_result_el.find("iof:Result", ns)
                bib_el = result_el.find("iof:BibNumber", ns)
                control_card_el = result_el.find("iof:ControlCard", ns)
                finish_time_el = result_el.find("iof:FinishTime", ns)

                splits = []
                for split in result_el.findall("iof:SplitTime", ns):
                    split_time_el = split.find("iof:Time", ns)
                    if split_time_el is not None:
                        control_code = split.find("iof:ControlCode", ns)
                        split_obj = {
                            "control_code": control_code.text,
                            "time": split_time_el.text,
                        }
                        splits.append(split_obj)

                result = {
                    "bib": (
                        result_el.find("iof:BibNumber", ns).text
                        if bib_el is not None
                        else ""
                    ),
                    "start_time": result_el.find("iof:StartTime", ns).text,
                    "finish_time": (
                        finish_time_el.text if finish_time_el is not None else ""
                    ),
                    "status": result_el.find("iof:Status", ns).text,
                    "control_card": (
                        control_card_el.text if control_card_el is not None else ""
                    ),
                    "splits": splits,
                }
                person_results.append(
                    {
                        "person": person,
                        "organization": organization,
                        "group": groups[group_id],
                        "result": result,
                    }
                )

        elif class_result.find("iof:TeamResult", ns):
            for team_result_el in class_result.findall("iof:TeamResult", ns):
                bib_number = team_result_el.find("iof:BibNumber", ns).text
                for team_member_result_el in team_result_el.findall(
                    "iof:TeamMemberResult", ns
                ):
                    person_el = team_member_result_el.find("iof:Person", ns)

                    if not person_el:
                        # Person element is omitted, no competitor on 2nd and 3rd leg,
                        # but TeamMemberResult elements for these legs must be present anyway
                        continue

                    birth_date_el = person_el.find("iof:BirthDate", ns)
                    id_el = person_el.find("iof:Id", ns)
                    person = {
                        "family": person_el.find("iof:Name", ns)
                        .find("iof:Family", ns)
                        .text,
                        "given": person_el.find("iof:Name", ns)
                        .find("iof:Given", ns)
                        .text,
                        "extensions": {},
                    }
                    if birth_date_el is not None:
                        person["birth_date"] = birth_date_el.text
                    if id_el is not None:
                        person["id"] = id_el.text

                    org_el = team_member_result_el.find("iof:Organisation", ns)
                    organization = None
                    if org_el:
                        organization = {"name": org_el.find("iof:Name", ns).text}
                        if org_el.find("iof:Id", ns):
                            organization["id"] = org_el.find("iof:Id", ns).text

                        role = org_el.find("iof:Role", ns)
                        if role:
                            role_person = role.find("iof:Person", ns)
                            organization["role_person"] = "{} {}".format(
                                role_person.find("iof:Name", ns)
                                .find("iof:Family", ns)
                                .text,
                                role_person.find("iof:Name", ns)
                                .find("iof:Given", ns)
                                .text,
                            )

                    result_el = team_member_result_el.find("iof:Result", ns)
                    leg = result_el.find("iof:Leg", ns).text
                    control_card_el = result_el.find("iof:ControlCard", ns)
                    finish_time_el = result_el.find("iof:FinishTime", ns)

                    splits = []
                    for split in result_el.findall("iof:SplitTime", ns):
                        split_time_el = split.find("iof:Time", ns)
                        if split_time_el is not None:
                            control_code = split.find("iof:ControlCode", ns)
                            split_obj = {
                                "control_code": control_code.text,
                                "time": split_time_el.text,
                            }
                            splits.append(split_obj)

                    final_bib = ""
                    if leg and bib_number and leg.isdigit() and bib_number.isdigit():
                        final_bib = str(int(leg) * 1000 + int(bib_number))

                    result = {
                        "bib": final_bib,
                        "start_time": result_el.find("iof:StartTime", ns).text,
                        "finish_time": (
                            finish_time_el.text if finish_time_el is not None else ""
                        ),
                        "status": result_el.find("iof:Status", ns).text,
                        "control_card": (
                            control_card_el.text if control_card_el is not None else ""
                        ),
                        "splits": splits,
                    }
                    person_results.append(
                        {
                            "person": person,
                            "organization": organization,
                            "group": groups[group_id],
                            "result": result,
                        }
                    )

    return person_results


def event(tree, ns):
    root = tree.getroot()
    event_obj = {"races": []}
    event_el = root.find("iof:Event", ns)

    if event_el is None:
        return

    if event_el.find("iof:Name", ns) is not None:
        event_obj["name"] = event_el.find("iof:Name", ns).text
    if event_el.find("iof:StartTime", ns) is not None:
        event_obj["start_time"] = event_el.find("iof:StartTime", ns).text
    if event_el.find("iof:URL", ns) is not None:
        event_obj["url"] = event_el.find("iof:URL", ns).text

    if event_el is not None:
        for race_el in event_el.findall("iof:Race", ns):
            race_obj = {
                "name": (
                    race_el.find("iof:Name", ns).text
                    if race_el.find("iof:Name", ns) is not None
                    else ""
                )
            }
            start_time_el = race_el.find("iof:StartTime", ns)
            if start_time_el:
                if start_time_el.find("iof:Date", ns) is not None:
                    race_obj["date"] = start_time_el.find("iof:Date", ns).text
                if start_time_el.find("iof:Time", ns) is not None:
                    race_obj["time"] = start_time_el.find("iof:Time", ns).text

            event_obj["races"].append(race_obj)

    return event_obj
