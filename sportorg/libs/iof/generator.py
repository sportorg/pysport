from datetime import datetime

from lxml.builder import E
from lxml.etree import Element, ElementTree

from sportorg.models.memory import Race, ResultStatus
from sportorg.models.result.result_calculation import ResultCalculation


def otime_to_str(race_obj, otime):
    """
    Convert time to the date string, expressed in ISO 8601 format.
    Day is taken from settings of race
    """
    day = race_obj.data.get_start_datetime()
    return day.strftime('%Y-%m-%d') + 'T' + otime.to_str(3)


def get_iof_status(status):
    """Convert to IOF status string"""
    if status == 1 or status == ResultStatus.OK or status == ResultStatus.RESTORED:
        return 'OK'
    elif status == ResultStatus.DID_NOT_START:
        return 'DidNotStart'
    elif status == ResultStatus.DID_NOT_FINISH:
        return 'DidNotFinish'

    return 'Disqualified'


def generate_result_list(obj, creator: str, all_splits: bool = False):
    """Generate the IOF XML ResultList string from the race data"""

    xmlns = 'http://www.orienteering.org/datastandard/3.0'
    xsi = 'http://www.w3.org/2001/XMLSchema-instance'

    xml_rl = Element(
        '{' + xmlns + '}ResultList',
        nsmap={'xsi': xsi, None: xmlns},
        iofVersion='3.0',
        creator=creator,
        createTime=datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
    )
    xml_rl.append(generate_evant(obj))

    for group in obj.groups:
        # Generate ClassResult and Class objects for each group

        xml_cr = E.ClassResult(generate_class(group))

        course = group.course
        if course:
            xml_cr.append(generate_course(course))

        xml_rl.append(xml_cr)

        if not group.is_relay():
            # individual race - PersonResult object
            for result in ResultCalculation(obj).get_group_finishes(group):
                person = result.person
                organization = person.organization

                xml_result = generate_result(obj, result, all_splits)

                # compose PersonResult from organization, person and result
                xml_person_result = E.PersonResult(
                    generate_person(person),
                    generate_organization(organization),
                    xml_result,
                )
                xml_cr.append(xml_person_result)

        else:
            # process relay race data - TeamResult-TeamMemberResult-Result
            for relay_team in ResultCalculation(obj).process_relay_results(group):
                organization = relay_team.legs[0].person.organization
                xml_team_result = E.TeamResult(
                    E.Name(organization.name if organization else ''),
                    generate_organization(organization),
                    E.BibNumber(str(relay_team.bib_number)),
                )
                xml_cr.append(xml_team_result)

                for team_member in relay_team.legs:
                    # relay team loop
                    person = team_member.person
                    result = team_member.result
                    organization = person.organization
                    course = obj.find_course(result)

                    # generate Result object
                    xml_result = E.Result(
                        E.Leg(str(team_member.leg)),
                        E.StartTime(otime_to_str(obj, result.get_start_time())),
                        E.FinishTime(otime_to_str(obj, result.get_finish_time())),
                        E.Time(str(result.get_result_otime().to_sec()) + '.0'),
                        E.Status(get_iof_status(result.status)),
                        E.OverallResult(
                            E.Time(
                                str(result.get_result_otime_relay().to_sec()) + '.0'
                            ),
                            E.Position(str(relay_team.place)),
                            E.Status(
                                get_iof_status(ResultStatus.DISQUALIFIED)
                                if relay_team.get_correct_lap_count() < team_member.leg
                                else get_iof_status(ResultStatus.OK)
                            ),
                        ),
                        generate_course(course),
                    )
                    # append splits to Result object
                    for split in result.splits:
                        xml_result.append(generate_split(split))

                    # compose TeamMemberResult
                    xml_team_member_result = E.TeamMemberResult(
                        generate_person(person),
                        generate_organization(organization),
                        xml_result,
                    )
                    xml_team_result.append(xml_team_member_result)

    return ElementTree(xml_rl)


def generate_entry_list(obj, creator: str):
    """Generate the IOF XML EntryList string from the race data"""

    xmlns = 'http://www.orienteering.org/datastandard/3.0'
    xsi = 'http://www.w3.org/2001/XMLSchema-instance'

    xml_el = Element(
        '{' + xmlns + '}EntryList',
        nsmap={'xsi': xsi, None: xmlns},
        iofVersion='3.0',
        creator=creator,
        createTime=datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
    )
    xml_el.append(generate_evant(obj))

    for person in obj.persons:
        # Generate PersonEntry objects for each person
        organization = person.organization
        group = person.group

        xml_pe = E.PersonEntry(
            generate_person(person),
            generate_organization(organization),
            generate_class(group),
        )
        xml_el.append(xml_pe)

    return ElementTree(xml_el)


def generate_start_list(obj, creator: str):
    """Generate the IOF XML StartList string from the race data"""

    if isinstance(obj, Race):
        xmlns = 'http://www.orienteering.org/datastandard/3.0'
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'

        xml_sl = Element(
            '{' + xmlns + '}StartList',
            nsmap={'xsi': xsi, None: xmlns},
            iofVersion='3.0',
            creator=creator,
            createTime=datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        )
        xml_sl.append(generate_evant(obj))

        for group in obj.groups:
            # Generate ClassStart and Class objects for each group
            xml_cs = E.ClassStart(generate_class(group))
            xml_sl.append(xml_cs)

            if not group.is_relay():
                # individual race - PersonStart object
                for person in obj.get_persons_by_group(group):
                    # generate Start
                    xml_start = E.Start(
                        E.StartTime(otime_to_str(obj, person.start_time)),
                        E.BibNumber(str(person.bib) if person.bib else ''),
                        E.ControlCard(str(person.card_number)),
                    )
                    # compose PersonStart from organization, person and result
                    xml_person_start = E.PersonStart(
                        generate_person(person),
                        generate_organization(person.organization),
                        xml_start,
                    )
                    xml_cs.append(xml_person_start)

            else:
                pass

    return ElementTree(xml_sl)


def generate_competitor_list(obj, creator: str):
    """Generate the IOF XML CompetitorList string from the race data"""

    if isinstance(obj, Race):
        xmlns = 'http://www.orienteering.org/datastandard/3.0'
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'

        xml_cl = Element(
            '{' + xmlns + '}CompetitorList',
            nsmap={'xsi': xsi, None: xmlns},
            iofVersion='3.0',
            creator=creator,
            createTime=datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        )
        xml_cl.append(generate_evant(obj))

        for person in obj.persons:
            # Generate Competitor object for each person

            xml_competitor = E.Competitor(generate_person(person))

            if person.organization:
                xml_competitor.append(generate_organization(person.organization))

            if person.group:
                xml_competitor.append(generate_class(person.group))

            xml_competitor.append(E.ControlCard(str(person.card_number)))

            xml_cl.append(xml_competitor)

    return ElementTree(xml_cl)


def generate_evant(obj):
    ret = E.Event(E.Name(obj.data.title if obj.data else 'Event'))
    return ret


def generate_organization(organization):
    ret = E.Organisation(
        E.Id(str(organization.id) if organization else ''),
        E.Name(organization.name if organization else ''),
        E.ShortName(organization.name if organization else ''),
    )
    return ret


def generate_person(person):
    person_name = person.name
    if not person_name or len(person_name) < 1:
        # mandatory first name (SPORTident Center doesn't work without it)
        person_name = '_'

    ret = E.Person(
        E.Id(str(person.world_code)),
        E.Name(
            E.Family(person.surname),
            E.Given(person_name),
        ),
    )
    if person.birth_date:
        ret.append(E.BirthDate(str(person.birth_date)))

    return ret


def generate_split(split):
    ret = E.SplitTime(
        E.ControlCode(str(split.code)), E.Time(str(split.relative_time.to_sec()))
    )
    return ret


def generate_class(group):
    short_name = group.name
    long_name = group.name
    if group.long_name:
        long_name = group.long_name

    name_limit = 64  # limit of LiveLox service
    if len(short_name) > name_limit:
        short_name = short_name[:name_limit]
    if len(long_name) > name_limit:
        long_name = long_name[:name_limit]

    ret = E.Class(E.Id(str(group.id)), E.Name(long_name), E.ShortName(short_name))
    return ret


def generate_course(course):
    ret = E.Course(
        E.Id(str(course.id) if course else ''),
        E.Name(course.name if course else ''),
        E.Length(str(course.length) if course else ''),
        E.NumberOfControls(str(len(course.controls)) if course else ''),
    )
    return ret


def generate_result(obj, result, all_controls=False):
    ret = E.Result(
        E.BibNumber(str(result.get_bib()) if result.get_bib() else ''),
        E.StartTime(otime_to_str(obj, result.get_start_time())),
        E.FinishTime(otime_to_str(obj, result.get_finish_time())),
        E.Time(str(result.get_result_otime().to_sec()) + '.0'),
        # E.TimeBehind(otime_to_str(obj, result.diff)),
        E.Position(str(result.place)),
        E.Status(get_iof_status(result.status)),
    )

    # add splits to Result object
    for split in result.splits:
        if all_controls or split.is_correct:
            ret.append(generate_split(split))

    ret.append(E.ControlCard(str(result.card_number)))

    # course = obj.find_course(result)
    # ret.append(generate_course(course))  # Livelox compatibility - moved to Class

    return ret
