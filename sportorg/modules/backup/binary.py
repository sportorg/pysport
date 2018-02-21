import pickle
import uuid

from sportorg import config
from sportorg.models import memory


def dump(file):
    data = {'version': config.VERSION}
    race = memory.race()

    data['id'] = str(race.id)
    data['data'] = race.data
    data['courses'] = race.courses
    data['groups'] = race.groups
    data['persons'] = race.persons
    data['results'] = race.results
    data['organizations'] = race.organizations
    data['settings'] = race.settings
    pickle.dump(data, file)


def load(file):
    data = pickle.load(file)
    if not ('version' in data):
        return
    # FIXME
    if True or data['version'] == config.VERSION:
        race = memory.race()
        if 'id' in data:
            race.id = uuid.UUID(data['id'])
        race.data = data['data']
        race.courses = data['courses']
        race.groups = data['groups']
        race.persons = data['persons']
        race.results = data['results']
        race.organizations = data['organizations']
        race.settings = data['settings']
