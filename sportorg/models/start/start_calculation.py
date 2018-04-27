from enum import Enum

from sportorg.models.memory import race, Group, RaceType


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

    @staticmethod
    def _sort_func(person):
        group = person.group
        assert isinstance(group, Group)
        if race().get_type(group) == RaceType.RELAY:
            return person.bib is None, person.bib % 1000 * 10 + person.bib // 1000
        else:
            return person.start_time is None, person.start_time


class ChessGenerator(GroupsStartList):
    pass


class PersonsGenerator:
    def __init__(self, persons, sorting=None):
        self._persons = persons
        self._sorting = sorting


class TeamStartList:
    def __init__(self, persons, sorting=None):
        self._persons = persons
        self._sorting = sorting


class TeamStatisticsList:
    def __init__(self, persons, sorting=None):
        self._persons = persons
        self._sorting = sorting
        self._group_list = []
        self._team_list = []

    def generate(self):
        self._create_group_list()
        self._create_team_list()
        return self

    def _create_group_list(self):
        self._group_list = []
        for person in self._persons:
            if person.group:
                cur_group = person.group
                if cur_group not in self._group_list:
                    self._group_list.append(cur_group)
        self._group_list.sort(key=lambda x: x.name)

    def _create_team_list(self):
        self._team_list = []
        for person in self._persons:
            if person.organization:
                cur_team = person.organization
                if cur_team not in self._team_list:
                    self._team_list.append(cur_team)
        self._team_list.sort(key=lambda x: x.name)
