from sportorg.libs.winorient import wo
from sportorg.models.memory import Qualification
from sportorg.models import memory
from sportorg.modules.winorient.wdb import WinOrientBinary


def import_csv(source):
    wo_csv = wo.parse_csv(source)
    race = memory.race()

    for group_name in wo_csv.groups:
        group = memory.create(memory.Group, name=group_name, long_name=group_name)
        race.groups.append(group)

    for team_name in wo_csv.teams:
        org = memory.create(memory.Organization, name=team_name)
        race.organizations.append(org)

    for person_dict in wo_csv.data:
        if person_dict['qual_id'].isdigit():
            qual = Qualification(int(person_dict['qual_id']))
        else:
            qual = 0
        person = memory.create(
            memory.Person,
            **person_dict,
            group=memory.find(race.groups, name=person_dict['group_name']),
            organization=memory.find(race.organizations, name=person_dict['team_name']),
            qual=qual
        )
        race.persons.append(person)


def import_wo_wdb(file_name):
    wb = WinOrientBinary(file=file_name)
    # wb.run()
    wb.create_objects()
