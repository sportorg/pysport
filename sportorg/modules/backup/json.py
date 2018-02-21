import json
from sportorg.models.memory import races


def dump(file):
    data = {
        'version': '1.0.0',
        'races': [e.to_dict() for e in races()]
    }
    json.dump(data, file, sort_keys=True, indent=2)


def load(file):
    data = json.load(file)

    # hack
    for race_dict in data['races']:
        race_dict['id'] = str(races()[0].id)

    for race_dict in data['races']:
        for r in races():
            if race_dict['id'] == str(r.id):
                r.update_data(race_dict)

