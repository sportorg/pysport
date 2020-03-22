from datetime import datetime
from lxml.builder import E
from lxml.etree import ElementTree, Element

from sportorg import config
from sportorg.models.memory import ResultStatus
from sportorg.models.result.result_calculation import ResultCalculation

def otime_to_str(race_obj, otime):
    """Convert time to the date string, expressed in ISO 8601 format. Day is taken from settings of race"""
    day = race_obj.data.start_datetime
    return day.strftime('%Y-%m-%d') + "T" + otime.to_str(3)

def get_iof_status(status):
    """Convert to IOF status string"""
    if status == 1 or status == ResultStatus.OK or status == ResultStatus.RESTORED:
        return "OK"
    elif status == ResultStatus.DID_NOT_START:
        return "DidNotStart"
    elif status == ResultStatus.DID_NOT_FINISH:
        return "DidNotFinish"

    return "Disqualified"

def generate_result_list(obj):
    """Generate the IOF XML ResultList string from the race data"""

    xmlns = "http://www.orienteering.org/datastandard/3.0"
    xsi = "http://www.w3.org/2001/XMLSchema-instance"

    xml_rl = Element('{' + xmlns  + '}ResultList',
                    nsmap={'xsi': xsi, None: xmlns},
                    iofVersion='3.0',
                    creator=config.NAME,
                    createTime=datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    )
    xml_rl.append(
        E.Event(
            E.Name(obj.data.title if obj.data else 'Event')
        )
    )

    for group in obj.groups:
        # Generate ClassResult and Class objects for each group

        xml_cr = E.ClassResult(
            E.Class(
                E.Id(str(group.id)),
                E.Name(group.long_name),
                E.ShortName(group.name),
            )
        )
        xml_rl.append(xml_cr)

        if not group.is_relay():
            # individual race - PersonResult object
            for result in ResultCalculation(obj).get_group_finishes(group):

                person = result.person
                organization = person.organization
                course = obj.find_course(result)

                # generate Result
                xml_result = E.Result(
                        E.StartTime(otime_to_str(obj, result.get_start_time())),
                        E.FinishTime(otime_to_str(obj, result.get_finish_time())),
                        E.Time(str(result.get_result_otime().to_sec()) + ".0"),
                        E.Position(str(result.place)),
                        E.Status(get_iof_status(result.status)),
                        # E.TimeBehind(otime_to_str(obj, result.diff)),
                        E.Course(
                            E.Id(str(course.id) if course else ''),
                            E.Name(course.name if course else ''),
                            E.Length(str(course.length) if course else ''),
                            E.NumberOfControls(str(len(course.controls)) if course else '')
                        )
                )

                # add splits to Result object
                for split in result.splits:
                    xml_result.append(
                        E.SplitTime(
                            E.ControlCode(str(split.code)),
                            E.Time(str(split.relative_time.to_sec()))
                        )
                    )

                # compose PersonResult from organization, person and result
                xml_person_result = E.PersonResult(
                    E.Person(
                        E.Id(str(person.world_code)),
                        E.Name(
                            E.Family(person.surname),
                            E.Given(person.name),
                        )
                    ),
                    E.Organisation(
                        E.Id(str(organization.id) if organization else ''),
                        E.Name(organization.name if organization else ''),
                        E.ShortName(organization.name if organization else '')
                    ),
                    xml_result
                )
                xml_cr.append(xml_person_result)

        else:
            # process relay race data - TeamResult-TeamMemberResult-Result
            for relay_team in ResultCalculation(obj).process_relay_results(group):
                organization = relay_team.legs[0].person.organization
                xml_team_result = E.TeamResult(
                    E.Name(organization.name if organization else ''),
                    E.Organisation(
                        E.Id(str(organization.id) if organization else ''),
                        E.Name(organization.name if organization else ''),
                        E.ShortName(organization.name if organization else '')
                    ),
                    E.BibNumber(str(relay_team.bib_number))
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
                        E.Time(str(result.get_result_otime().to_sec()) + ".0"),
                        E.Status(get_iof_status(result.status)),
                        E.OverallResult(
                            E.Time(str(result.get_result_otime_relay().to_sec()) + ".0"),
                            E.Position(str(relay_team.place)),
                            E.Status(get_iof_status(ResultStatus.DISQUALIFIED)
                                     if relay_team.get_correct_lap_count() < team_member.leg
                                     else get_iof_status(ResultStatus.OK)
                            ),
                        ),
                        E.Course(
                            E.Id(str(course.id) if course else ''),
                            E.Name(course.name if course else ''),
                            E.Length(str(course.length) if course else ''),
                            E.NumberOfControls(str(len(course.controls)) if course else '')
                        )
                    )
                    # append splits to Result object
                    for split in result.splits:
                        xml_result.append(
                            E.SplitTime(
                                E.ControlCode(str(split.code)),
                                E.Time(str(split.relative_time.to_sec()))
                            )
                        )

                    # compose TeamMemberResult
                    xml_team_member_result = E.TeamMemberResult(
                        E.Person(
                            E.Id(str(person.world_code)),
                            E.Name(
                                E.Family(person.surname),
                                E.Given(person.name),
                            )
                        ),
                        E.Organisation(
                            E.Id(str(organization.id) if organization else ''),
                            E.Name(organization.name if organization else ''),
                            E.ShortName(organization.name if organization else '')
                        ),
                        xml_result,
                    )
                    xml_team_result.append(xml_team_member_result)

    return ElementTree(xml_rl)