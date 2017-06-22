import os

from sportorg.app.models.memory import race, Result, Person
from sportorg.app.models.result_calculation import ResultCalculation
from sportorg.lib.template import template
import config


def get_templates(path=None):
    if path is None:
        path = config.TEMPLATE_DIR
    files = list()
    for p in os.listdir(path):
        full_path = os.path.join(path, p)
        if os.path.isdir(full_path):
            fs = get_templates(full_path)
            for f in fs:
                files.append(f)
        else:
            files.append(full_path)

    return files


def get_text(**kwargs):
    return get_text_from_file(config.template_dir('main.html'), **kwargs)


def get_text_from_file(path, **kwargs):
    return template.get_text_from_file(path, **kwargs)


def get_start_list_data():
    pass


def get_result_data():
    ret = {}
    data = {}
    for group in race().groups:
        array = ResultCalculation().get_group_finishes(group)
        group_data = []
        for res in array:
            assert isinstance(res, Result)
            person_data = get_person_result_data(res)
            group_data.append(person_data)
        data[group.name] = group_data
    ret['data'] = data
    ret['title'] = 'Competition title'
    ret['table_titles'] = ['name', 'team', 'qual', 'year', 'result', 'place']

    return ret


def get_splits_data():
    pass


def get_entry_statistics_data():
    pass


def get_team_statistics_data():
    pass


def get_person_result_data(res):
    ret = []
    person = res.person
    assert isinstance(person, Person)
    ret.append(person.surname + ' ' + person.name)
    ret.append(person.organization.name)
    ret.append(person.qual)
    ret.append(person.year)
    ret.append(res.get_result())
    ret.append(res.place)
    return ret
