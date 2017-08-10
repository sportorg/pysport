import pickle

from sportorg.app.models import memory
from sportorg import config


def dump(file):
    data = dict()
    data['version'] = config.VERSION
    data['data'] = memory.race().data
    data['courses'] = memory.race().courses
    data['groups'] = memory.race().groups
    data['persons'] = memory.race().persons
    data['results'] = memory.race().results
    data['organizations'] = memory.race().organizations
    data['settings'] = memory.race().settings
    pickle.dump(data, file)


def load(file):
    data = pickle.load(file)
    if not ('version' in data):
        return
    if data['version'] == config.VERSION:
        memory.race().update(
            data=data['data'],
            courses=data['courses'],
            groups=data['groups'],
            persons=data['persons'],
            results=data['results'],
            organizations=data['organizations'],
            settings=data['settings']
        )
