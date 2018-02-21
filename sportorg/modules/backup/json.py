import json
import uuid

from sportorg import config
from sportorg.models.memory import races, race, new_event


def dump(file):
    data = {
        'version': config.VERSION.file,
        'races': [e.to_dict() for e in races()]
    }
    json.dump(data, file, sort_keys=True, indent=2)


def load(file):
    data = json.load(file)
    event = []
    for race_dict in data['races']:
        obj = race()
        obj.id = uuid.UUID(str(race_dict['id']))
        obj.update_data(race_dict)
        event.append(obj)
    new_event(event)
