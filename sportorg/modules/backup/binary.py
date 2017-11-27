import pickle

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.models import memory


def dump(file, create=False):
    data = {'version': config.VERSION}
    if create:
        race = memory.Race()
    else:
        race = memory.race()

    data['data'] = race.data
    data['courses'] = race.courses
    data['groups'] = race.groups
    data['persons'] = race.persons
    data['results'] = race.results
    data['organizations'] = race.organizations
    data['settings'] = race.settings
    pickle.dump(data, file)

    # apply filters again
    GlobalAccess().apply_filters()


def load(file):
    data = pickle.load(file)
    if not ('version' in data):
        return
    # FIXME
    if True or data['version'] == config.VERSION:
        race = memory.race()
        race.data = data['data']
        race.courses = data['courses']
        race.groups = data['groups']
        race.persons = data['persons']
        race.results = data['results']
        race.organizations = data['organizations']
        race.settings = data['settings']
