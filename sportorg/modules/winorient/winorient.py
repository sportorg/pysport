from sportorg.libs.winorient import wo
from sportorg.models.memory import Qualification
from sportorg.models import memory
from sportorg.modules.winorient.wdb import WinOrientBinary


def import_csv(source):
    wo_csv = wo.parse_csv(source)
    race = memory.race()

    for group_name in wo_csv.groups:
        group = memory.find(race.groups, name=group_name)
        if group is None:
            group = memory.Group()
            group.name = group_name
            group.long_name = group_name
            race.groups.append(group)

    for team_name in wo_csv.teams:
        org = memory.find(race.organizations, name=team_name)
        if org is None:
            org = memory.Organization()
            org.name = team_name
            race.organizations.append(org)

    for person_dict in wo_csv.data:
        if person_dict['qual_id'] and person_dict['qual_id'].isdigit():
            qual_id = int(person_dict['qual_id'])
        else:
            qual_id = 0
        person_org = memory.find(race.organizations, name=person_dict['team_name'])
        person_org.contact.value = person_dict['representative']

        person = memory.Person()
        person.name = person_dict['name']
        person.surname = person_dict['surname']
        person.bib = person_dict['bib']
        person.set_year(person_dict['year'])
        person.card_number = person_dict['sportident_card']
        person.group = memory.find(race.groups, name=person_dict['group_name'])
        person.organization = person_org
        person.qual = Qualification(qual_id)
        person.comment = person_dict['comment']
        race.persons.append(person)


def import_wo_wdb(file_name):
    wb = WinOrientBinary(file=file_name)
    # wb.run()
    wb.create_objects()
