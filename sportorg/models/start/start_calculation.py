from enum import Enum

from sportorg.models.memory import race, Group, RaceType, find
from sportorg.utils.time import time_to_hhmmss


class SortType(Enum):
    BIB = 0
    ORGANIZATION = 1
    GROUP = 2
    START = 3
    NAME = 4

    def __str__(self):
        return "%s" % self._name_

    def __repr__(self):
        return self.__str__()


class PersonSort:
    def __init__(self, persons):
        self._persons = persons
        self._sorting = SortType.BIB

    def set_sorting(self, sorting=None):
        if sorting is not None:
            self._sorting = sorting
        return self

    def sort(self, sorting=None, reverse=False):
        if sorting is not None:
            self._sorting = sorting
        if self._sorting == SortType.BIB:
            self._persons.sort(key=lambda person: (person.bib == 0, person.bib), reverse=reverse)
        elif self._sorting == SortType.ORGANIZATION:
            self._persons.sort(key=lambda person: person.organization.name if person.organization is not None else '',
                               reverse=reverse)
        elif self._sorting == SortType.GROUP:
            self._persons.sort(key=lambda person: person.group.name if person.group is not None else '',
                               reverse=reverse)
        elif self._sorting == SortType.START:
            self._persons.sort(key=lambda person: (person.start_time is None, person.start_time),
                               reverse=reverse)
        elif self._sorting == SortType.NAME:
            self._persons.sort(key=lambda person: (person.full_name == '', person.full_name),
                               reverse=reverse)


class GroupsStartList:
    def __init__(self, persons):
        self._group = {}
        self._noname_group = []
        self._persons = persons
        self._first_time = None
        self._last_time = None

    @property
    def first_time(self):
        if self._first_time is None:
            self._gen_time()
        return self._first_time

    @property
    def last_time(self):
        if self._last_time is None:
            self._gen_time()
        return self._last_time

    def _gen_time(self):
        if len(self._persons) == 0:
            return
        first_time = self._persons[0].start_time
        last_time = self._persons[0].start_time
        for person in self._persons:
            if person.start_time is not None:
                if first_time > person.start_time:
                    first_time = person.start_time
                if last_time < person.start_time:
                    last_time = person.start_time
        self._first_time = first_time
        self._last_time = last_time

    def _groups_generate(self):
        for person in self._persons:
            if person.group is not None:
                if person.group.name not in self._group:
                    self._group[person.group.name] = [person]
                else:
                    self._group[person.group.name].append(person)
            else:
                self._noname_group.append(person)

        return self

    def _sort_group(self, group_name):
        self._group[group_name].sort(key=self._sort_func)
        return self

    def _sort_noname_group(self):
        self._noname_group.sort(key=self._sort_func)
        return self

    def _sort_persons(self):
        for group_name in self._group.keys():
            self._sort_group(group_name)

        return self

    def get_list(self):
        ret = []
        group_names = list(self._groups_generate()._sort_persons()._group.keys())
        group_names.sort()
        for group_name in group_names:
            group_obj = find(race().groups, name=group_name)
            group = {
                'name': group_name,
                'type': race().get_type(group_obj).name,
                'persons': []
            }
            for person in self._group[group_name]:
                group['persons'].append(person.to_dict())
            ret.append(group)

        return ret

    def _get_person_list(self):
        persons_data = []
        self._persons.sort(key=self._sort_func)
        for person in self._persons:
            persons_data.append(person.to_dict())

        return persons_data

    @staticmethod
    def _sort_func(person):
        group = person.group
        assert isinstance(group, Group)
        if race().get_type(group) == RaceType.RELAY:
            return person.bib is None, person.bib % 1000 * 10 + person.bib // 1000
        else:
            return person.start_time is None, person.start_time



class ChessGenerator(GroupsStartList):
    def get_list(self):
        cache = set()
        data = {}
        self._persons.sort(key=self._sort_func)
        for person in self._persons:
            if person.start_time is None:
                continue
            time = time_to_hhmmss(person.start_time)
            if time not in cache:
                data[time] = [person.to_dict()]
            else:
                data[time].append(person.to_dict())
            cache.add(time)

        for time in data.keys():
            data[time].sort(key=lambda val: (val['bib'] is None, val['bib']))

        return data


class PersonsGenerator:
    def __init__(self, persons, sorting=None):
        self._persons = persons
        self._sorting = sorting

    def get_list(self):
        persons_data = []
        PersonSort(self._persons).sort(self._sorting)
        for person in self._persons:
            persons_data.append(person.to_dict())

        return persons_data


class TeamStartList:
    def __init__(self, persons, sorting=None):
        self._persons = persons
        self._sorting = sorting

    def _get_teams(self):
        team_persons = {}
        for person in self._persons:
            if person.organization:
                if person.organization.id not in team_persons:
                    team_persons[person.organization.id] = {
                        'persons': [],
                        'team': person.organization
                    }
                team_persons[person.organization.id]['persons'].append(person)
        return team_persons

    def get_list(self):
        """
        :return: [
            {
                "name": str,
                "price": int,
                "persons": [
                    ...
                ]
            },
            ...
        ]
        """
        data = []
        for _, team in self._get_teams().items():

            data_team = {
                'name': team['team'].name,
                'price': 0,
                'persons': []
            }
            PersonSort(team['persons']).sort(self._sorting)
            for person in team['persons']:
                if person.group:
                    data_team['price'] += person.group.price
                data_team['persons'].append(person.to_dict())
            data.append(data_team)
        data.sort(key=lambda x: x['name'].lower())
        return data


def get_start_data():
    start_list = GroupsStartList(race().persons)
    groups = start_list.get_list()
    ret = {
        'race': race().to_dict(),
        'groups': groups
    }

    return ret


def get_chess_list():
    start_list = ChessGenerator(race().persons)
    return start_list.get_list()


def get_persons_data(sorting=None):
    return {
        'race': race().to_dict(),
        'persons': PersonsGenerator(race().persons, sorting).get_list()
    }


def get_teams_data():
    return {
        'race': race().to_dict(),
        'teams': TeamStartList(race().persons, SortType.NAME).get_list()
    }
