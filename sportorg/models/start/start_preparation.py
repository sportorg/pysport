import logging
import math
import random
from datetime import timedelta
from sportorg.core.otime import OTime

from sportorg.models.memory import race, Group, Person


class ReserveManager(object):
    def __init__(self, r):
        self.race = r
    """
        Inserts reserve athletes into each group
        You can specify minimum quantity of person or percentage to add in each group
        Reserve record is marked with prefix, that can be specified by user

        Now effect on all groups, but in future we'll possible implement working with selected groups only
    """
    def process(self, reserve_prefix, reserve_count, reserve_percent):
        current_race = self.race

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
    def __init__(self, r):
        self.race = r
        self.person_array = []
        self.mix_groups = False
        self.split_regions = False
        self.split_teams = False
        self.split_start_groups = False

    def process(self, split_start_groups, split_teams, split_regions, mix_groups=False):
        current_race = self.race
        current_race.update_counters()

        self.mix_groups = mix_groups
        self.split_start_groups = split_start_groups
        self.split_teams = split_teams
        self.split_regions = split_regions

        # create temporary array
        self.person_array = []
        self.person_array = self.person_array

        for i in range(len(current_race.persons)):
            current_person = current_race.persons[i]
            assert isinstance(current_person, Person)
            index = i
            group = ''
            if current_person.group:
                group = current_person.group.name
            start_group = current_person.start_group
            team = ''
            region = ''
            if current_person.organization is not None:
                team = current_person.organization.name
                region = current_person.organization.address.state

            self.person_array.append([index, group, '{:03}'.format(start_group), team, region])

        # shuffle
        random.shuffle(self.person_array)
        random.shuffle(self.person_array)

        # sort array by group and start_group
        if mix_groups:
            if split_start_groups:
                self.person_array = sorted(self.person_array, key=lambda item: str(item[2]))
        else:
            if split_start_groups:
                self.person_array = sorted(self.person_array, key=lambda item: str(item[1]) + str(item[2]))
            else:
                self.person_array = sorted(self.person_array, key=lambda item: str(item[1]))

        # process team and region conflicts in each start group
        self.process_conflicts()

        # apply to model
        index_array = []
        for i in self.person_array:
            index_array.append(i[0])
        current_race.persons = [current_race.persons[x] for x in index_array]

    def process_conflicts(self):
        start = 0
        while start < len(self.person_array):

            if self.split_start_groups:
                end = self.get_last_index_in_start_group(start)
            else:
                if self.mix_groups:
                    end = len(self.person_array) - 1
                else:
                    end = self.get_last_index_in_group(start)

            self.process_conflicts_interval(start, end)
            start = end + 1

    def process_conflicts_interval(self, start, end):
        if self.split_teams or self.split_regions:
            i = start
            run = True
            while run:
                if i >= end:
                    # no conflicts till the end!
                    return True

                if self.conflict(i, i + 1):
                    j = i + 2
                    while j != i:

                        # boundary processing
                        if j > end:
                            # go to the beginning of array
                            j = start
                            if j == i:
                                break

                        if self.conflict(i, j):
                            j += 1
                        else:
                            # j index is a solution to split conflicting pair
                            break

                    if j == i:
                        # no solution found
                        print('no solution found')
                        return False
                    else:
                        # insert j after checked_index i
                        assert isinstance(self.person_array, list)
                        tmp = self.person_array.pop(j)
                        if j < i:
                            i -= 1
                        self.person_array.insert(i + 1, tmp)
                i += 1

    def conflict(self, i, j):
        conflict = False
        cur_team = self.person_array[i][3]
        cur_region = self.person_array[i][4]
        next_team = self.person_array[j][3]
        next_region = self.person_array[j][4]
        if self.split_teams and cur_team == next_team:
            conflict = True
        if self.split_regions and cur_region == next_region:
            conflict = True
        return conflict

    def get_first_index_in_group(self, search_index):
        k = search_index
        current_group = self.person_array[k][1]
        while k >= 0 and self.person_array[k][1] == current_group:
            k -= 1
        return k + 1

    def get_last_index_in_group(self, search_index):
        k = search_index
        current_group = self.person_array[k][1]
        while k < len(self.person_array) and self.person_array[k][1] == current_group:
            k += 1
        return k - 1

    def get_first_index_in_start_group(self, search_index):
        k = search_index
        current_group = self.person_array[k][2]
        while k >= 0 and self.person_array[k][2] == current_group:
            k -= 1
        return k + 1

    def get_last_index_in_start_group(self, search_index):
        k = search_index
        current_group = self.person_array[k][2]
        while k < len(self.person_array) and self.person_array[k][2] == current_group:
            k += 1
        return k - 1


class StartNumberManager(object):

    def __init__(self, r):
        self.race = r
    """
        Assign new start numbers

    """
    def process(self, is_interval, first_number=None, interval=None, mix_groups=False):
        if is_interval:
            cur_num = first_number
            for cur_corridor in get_corridors():
                if mix_groups:
                    cur_num = self.process_corridor(cur_corridor, cur_num, interval)
                else:
                    for cur_group in get_groups_by_corridor(cur_corridor):
                        cur_num = self.process_group(cur_group, cur_num, interval)
        else:
            corridors = get_corridors()
            first_number = 1  # TODO calculate from first start minute
            cur_num = first_number
            for cur_corridor in corridors:
                groups = get_groups_by_corridor(cur_corridor)
                for cur_group in groups:
                    cur_num = self.process_group_number_by_minute(cur_group, cur_num) + 1
                cur_num = cur_num - (cur_num % 100) + 100

    def process_group(self, group, first_number, interval):
        current_race = self.race
        persons = current_race.get_persons_by_group(group)
        current_num = first_number
        if persons is not None:
            for current_person in persons:
                current_person.bib = current_num
                current_num += interval
        return current_num

    def process_corridor(self, corridor, first_number, interval):
        current_race = self.race
        persons = current_race.get_persons_by_corridor(corridor)
        current_num = first_number
        if persons is not None:
            for current_person in persons:
                current_person.bib = current_num
                current_num += interval
        return current_num

    def process_group_number_by_minute(self, group, first_number):
        current_race = self.race
        persons = current_race.get_persons_by_group(group)
        if persons is not None and len(persons) > 0:
            first_start = persons[0].start_time
            minute = first_start.minute
            min_num = int(first_number / 100) * 100 + minute
            if min_num < first_number:
                min_num += 100

            for current_person in persons:
                start_time = current_person.start_time
                time_delta = (start_time - first_start)
                delta = time_delta.to_sec() // 60
                current_person.bib = int(min_num + delta)
            return persons[-1].bib

        return first_number


class StartTimeManager(object):

    def __init__(self, r):
        self.race = r
    """
        Set new start time for athletes

    """
    def process(self, corridor_first_start, is_group_start_interval, fixed_start_interval=None, mix_groups=False):
        current_race = self.race
        current_race.update_counters()

        corridors = get_corridors()
        for cur_corridor in corridors:
            cur_start = corridor_first_start

            if mix_groups:
                self.process_corridor(cur_corridor, cur_start, fixed_start_interval)
            else:
                groups = get_groups_by_corridor(cur_corridor)
                for cur_group in groups:
                    assert isinstance(cur_group, Group)
                    start_interval = fixed_start_interval

                    # try to take start interval from group properties
                    if is_group_start_interval:
                        if cur_group.start_interval is not None:
                            start_interval = cur_group.start_interval

                    cur_start = self.process_group(cur_group, cur_start, start_interval)

    def process_group(self, group, first_start, start_interval):
        current_race = self.race
        persons = current_race.get_persons_by_group(group)
        current_start = first_start
        if persons is not None:
            for current_person in persons:
                current_person.start_time = current_start
                current_start = current_start + start_interval
        return current_start

    def process_corridor(self, corridor, first_start, start_interval):
        current_race = self.race
        persons = current_race.get_persons_by_corridor(corridor)
        if persons is not None:
            current_start = first_start
            for current_person in persons:
                current_person.start_time = current_start
                current_start = current_start + timedelta(seconds=start_interval.second, minutes=start_interval.minute)


def get_selected_list():
    pass


def get_corridors():
        current_race = race()
        ret = []
        for current_group in current_race.groups:
            assert isinstance(current_group, Group)
            cur_corridor = current_group.start_corridor
            if not cur_corridor:
                cur_corridor = 0
            if cur_corridor not in ret:
                ret.append(cur_corridor)
        return sorted(ret)


def get_groups_by_corridor(corridor):
    current_race = race()
    ret = []
    for current_group in current_race.groups:
        assert isinstance(current_group, Group)
        cur_corridor = current_group.start_corridor
        if not cur_corridor:
            cur_corridor = 0
        if cur_corridor == corridor:
            ret.append(current_group)
    return sorted(ret, key=lambda item: item.order_in_corridor)


def guess_courses_for_groups():
    obj = race()
    for cur_group in obj.groups:
        assert isinstance(cur_group, Group)
        if not cur_group.course or True:  # TODO check empty courses after export!
            for cur_course in obj.courses:
                course_name = cur_course.name
                group_name = cur_group.name
                if str(course_name).find(group_name) > -1:
                    cur_group.course = cur_course
                    logging.debug('Connecting: group ' + group_name + ' with course ' + course_name)
                    break


def guess_corridors_for_groups():
    obj = race()
    course_index = 1
    for cur_course in obj.courses:
        cur_course.corridor = course_index
        course_index += 1

    for cur_group in obj.groups:
        assert isinstance(cur_group, Group)
        if cur_group.course:
            cur_group.start_corridor = cur_group.course.corridor


def change_start_time(if_add, time_offset):
    obj = race()
    for person in obj.persons:
        if person.start_time is None:
            person.start_time = OTime()
        if if_add:
            person.start_time = person.start_time + time_offset
        else:
            person.start_time = person.start_time - time_offset
