import pickle
import uuid

from sportorg import config
from sportorg.models import memory


def dump(file):
    data = {'version': config.VERSION}
    obj = memory.race()

    data['id'] = str(obj.id)
    data['data'] = obj.data
    data['courses'] = obj.courses
    data['groups'] = obj.groups
    data['persons'] = obj.persons
    data['results'] = obj.results
    data['organizations'] = obj.organizations
    data['settings'] = obj.settings
    pickle.dump(data, file)


def load(file):
    data = pickle.load(file)
    if not ('version' in data):
        return
    # FIXME
    if True or data['version'] == config.VERSION:
        obj = memory.race()
        if 'id' in data:
            obj.id = uuid.UUID(data['id'])
        obj.data = data['data']
        obj.courses = data['courses']
        obj.groups = data['groups']
        obj.persons = data['persons']
        obj.results = data['results']
        obj.organizations = data['organizations']
        obj.settings = data['settings']
