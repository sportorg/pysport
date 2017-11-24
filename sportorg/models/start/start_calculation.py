from sportorg.modules.utils.utils import if_none, time_to_hhmmss
from sportorg.models.memory import race


class GroupsStartList(object):
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

    def get_group_list(self, name_noname=None):
        """

        :return: [
            {
                "name": str,
                "persons": [
                    self._get_person_data,
                    ...
                ]
            }
        ]
        """
        result = []
        group_names = list(self._groups_generate()._sort_persons()._group.keys())
        group_names.sort()
        for group_name in group_names:
            group = {
                'name': group_name,
                'persons': []
            }
            for person in self._group[group_name]:
                group['persons'].append(self._get_person_data(person))
            result.append(group)

        if name_noname is not None:
            if len(self._noname_group) == 0:
                return result
            noname_group = {
                'name': name_noname,
                'persons': []
            }
            for person in self._sort_noname_group()._noname_group:
                noname_group['persons'].append(self._get_person_data(person))

        return result

    def get_person_list(self):
        """

        :return: [
            self._get_person_data,
            ...
        ]
        """
        result = []
        self._persons.sort(key=self._sort_func)
        for person in self._persons:
            result.append(self._get_person_data(person))

        return result

    @staticmethod
    def _sort_func(person):
        return person.start_time is None, person.start_time

    @staticmethod
    def _get_person_data(person):
        return {
            'name': person.full_name,
            'bib': person.bib,
            'team': person.organization.name if person.organization is not None else '',
            'qual': person.qual.get_title(),
            'year': if_none(person.year, ''),
            'sportident_card': str(person.sportident_card) if person.sportident_card is not None else '',
            'start': time_to_hhmmss(person.start_time)

        }


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
                data[time] = [self._get_person_data(person)]
            else:
                data[time].append(self._get_person_data(person))
            cache.add(time)

        for time in data.keys():
            data[time].sort(key=lambda val: (val['bib'] is None, val['bib']))

        return data


def get_start_data():
    """

    :return: {
        "title": str,
        "groups": [
            {
                "name": str,
                "persons": [
                    GroupsStartList _get_person_data
                    ...
                ]
            }
        ]
    }
    """
    start_list = GroupsStartList(race().persons)
    groups = start_list.get_group_list()
    result = {
        'title': race().get_setting('sub_title'),
        'groups': groups
    }

    return result


def get_chess_list():
    start_list = ChessGenerator(race().persons)
    return start_list.get_list()

