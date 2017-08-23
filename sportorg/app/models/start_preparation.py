import math
import random

from PyQt5.QtCore import QTime

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
    """
        Assign new start numbers

    """
    def process(self, is_interval, first_number=None, interval=None):
        pass


class StartTimeManager(object):
    """
        Set new start time for athletes

    """
    def process(self, corridor_first_start, is_start_interval, fixed_start_interval=None):
        current_race = race()
        current_race.update_counters()

        corridors = self.get_corridors()
        for cur_corridor in corridors:
            cur_start = corridor_first_start
            groups = self.get_groups_by_corridor(cur_corridor)
            for cur_group in groups:
                assert isinstance(cur_group, Group)
                start_interval = fixed_start_interval
                if  not is_start_interval:
                    if cur_group.start_interval is not None:
                        start_interval = cur_group.start_interval
                self.process_group(cur_group, cur_start, start_interval)

                # TODO cur_start += start_interval * cur_group.count_person
                for i in range (cur_group.count_person):
                    cur_start.addMSecs(start_interval.msec())


    def get_corridors(self):
        current_race = race()
        ret = []
        for current_group in current_race.groups:
            assert isinstance(current_group, Group)
            cur_corridor = current_group.start_corridor
            if cur_corridor not in ret:
                ret.append(cur_corridor)
        return sorted(ret)

    def get_groups_by_corridor(self, corridor):
        current_race = race()
        ret = []
        for current_group in current_race.groups:
            assert isinstance(current_group, Group)
            cur_corridor = current_group.start_corridor
            if cur_corridor == corridor:
                ret.append(current_group)
        return sorted(ret, key=lambda item: item.order_in_corridor)

    def process_group(self, group, first_start, start_interval):
        current_race = race()
        persons = current_race.get_persons_by_group(group)
        if persons is not None:
            current_start = first_start
            for current_person in persons:
                current_person.start_time = current_start
                assert isinstance(current_start, QTime)
                current_start.addMSecs(start_interval.msec())

def get_selected_list():
    pass
