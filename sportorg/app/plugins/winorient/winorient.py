import time
from sportorg.app.models import model
from sportorg.lib.winorient import wo


def import_csv(source):
    wo_csv = wo.parse_csv(source)

    diff = time.time()

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

    print(time.time()-diff)

    return True
