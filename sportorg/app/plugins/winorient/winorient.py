from sportorg.app.models import model
from sportorg.app.models import memory
from sportorg.lib.winorient import wo


def import_csv_to_model(source):
    wo_csv = wo.parse_csv(source)

    data_group = [{'name': group, 'long_name': group} for group in wo_csv.groups]
    model_group = {}
    with model.database_proxy.atomic():
        for data_dict in data_group:
            group = model.Group.create(**data_dict)
            model_group[group.name] = group.id

    data_team = [{'name': team} for team in wo_csv.teams]
    model_team = {}
    with model.database_proxy.atomic():
        for data_dict in data_team:
            org = model.Organization.create(**data_dict)
            model_team[org.name] = org.id

    data_person = []
    for p in wo_csv.data:
        p['group'] = model_group[p['group']]
        p['team'] = model_team[p['team']]
        data_person.append(p)
    with model.database_proxy.atomic():
        for data_dict in data_person:
            person = model.Person.create(**data_dict)
            participation = {
                "person": person,
                "group": data_dict['group']
            }
            if data_dict['card']:
                participation['control_card'] = model.ControlCard.create(
                    name="SPORTIDENT",
                    value=data_dict['card'],
                    person=person
                )

            model.Participation.create(**participation)

    return True


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
        person = memory.create(
            memory.Person,
            **person_dict,
            group=memory.find(race.groups, name=person_dict['group_name']),
            organization=memory.find(race.organizations, name=person_dict['team_name'])
        )
        race.persons.append(person)
