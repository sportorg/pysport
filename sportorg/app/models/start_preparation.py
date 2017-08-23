import math
import random

from sportorg.app.models.memory import race, Group, Person


class ReserveManager(object):
    """
        Inserts reserve athletes into each group
        You can specify minimum quantity of person or percentage to add in each group
        Reserve record is marked with prefix, that can be specified by user

        Now effect on all groups, but in future we'll possible implement working with selected groups only
    """
    def process(self, reserve_prefix, reserve_count, reserve_percent):
        current_race = race()
        current_race.update_counters()

        for current_group in current_race.groups:
            assert isinstance(current_group, Group)
            count = current_group.count_person

            percent_count = math.ceil(count * reserve_percent / 100)
            persons = current_race.get_persons_by_group(current_group)

            existing_reserves = 0
            if count > 0:
                for current_person in persons:
                    assert isinstance(current_person, Person)
                    str_name = "" + str(current_person.surname) + str(current_person.name)
                    if str.find(str_name, reserve_prefix) > -1:
                        existing_reserves += 1

            insert_count = max(reserve_count, percent_count) - existing_reserves

            for i in range(insert_count):
                new_person = Person()
                new_person.surname = reserve_prefix
                new_person.group = current_group
                current_race.persons.append(new_person)


class DrawManager(object):
    """
        Execute draw in each group
        Now effect on all groups, but in future we'll possible implement working with filtered persons
    """
    def process(self, split_start_groups, split_teams, split_regions):
        current_race = race()
        current_race.update_counters()

        # create temporary array
        person_array = []

        for i in range(len(current_race.persons)):
            current_person = current_race.persons[i]
            assert isinstance(current_person, Person)
            index = i
            group = current_person.group.name
            start_group = current_person.start_group
            team = ''
            region = ''
            if current_person.organization is not None:
                team = current_person.organization.name
                region = current_person.organization.region

            person_array.append([index, group, start_group, team, region])

        # shuffle
        random.shuffle(person_array)
        random.shuffle(person_array)

        # sort array by group and start_group
        if split_start_groups:
            person_array = sorted(person_array, key=lambda item: str(item[1]) + str(item[2]))
        else:
            person_array = sorted(person_array, key=lambda item: str(item[1]))

        # TODO process team and region conflicts in each start group

        # apply to model
        index_array = []
        for i in person_array:
            index_array.append(i[0])
        current_race.persons = [current_race.persons[x] for x in index_array]


class StartNumberManager(object):
    def process(self, is_interval, first_number=None, interval=None):
        pass


class StartTimeManager(object):
    def process(self, corridor_first_start, is_start_interval, fixed_start_interval=None):
        pass


def get_selected_list():
    pass
