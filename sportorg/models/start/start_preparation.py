import logging
import math
import random
import uuid
from copy import copy

from sportorg.common.otime import OTime
from sportorg.models.memory import Person, race
from sportorg.models.result.result_calculation import ResultCalculation


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
            count = current_group.count_person

            percent_count = math.ceil(count * reserve_percent / 100)
            persons = current_race.get_persons_by_group(current_group)

            existing_reserves = 0
            if count > 0:
                for current_person in persons:
                    str_name = (
                        '' + str(current_person.surname) + str(current_person.name)
                    )
                    if str.find(str_name, reserve_prefix) > -1:
                        existing_reserves += 1

            insert_count = int(max(reserve_count, percent_count) - existing_reserves)

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

    def set_array(self, persons):
        self.person_array = []

        for i in range(len(persons)):
            current_person = persons[i]
            index = i
            group = ''
            if current_person.group:
                group = current_person.group.name
            start_group = current_person.start_group
            team = ''
            region = ''
            if current_person.organization:
                team = current_person.organization.name
                region = current_person.organization.region

            self.person_array.append(
                [index, group, '{:03}'.format(start_group), team, region]
            )

    def get_tossed_array(self, persons):
        index_array = []
        for i in self.person_array:
            index_array.append(i[0])
        ret = [persons[x] for x in index_array]
        return ret

    def process(self, split_start_groups, split_teams, split_regions, mix_groups=False):
        current_race = self.race
        current_race.update_counters()
        ret = self.process_array(
            current_race.persons,
            split_start_groups,
            split_teams,
            split_regions,
            mix_groups,
        )
        current_race.persons = ret

    def process_array(
        self, persons, split_start_groups, split_teams, split_regions, mix_groups=False
    ):
        self.mix_groups = mix_groups
        self.split_start_groups = split_start_groups
        self.split_teams = split_teams
        self.split_regions = split_regions

        # create temporary array
        self.set_array(persons)

        # shuffle
        random.shuffle(self.person_array)
        random.shuffle(self.person_array)

        # sort array by group and start_group
        if mix_groups:
            if split_start_groups:
                self.person_array = sorted(
                    self.person_array, key=lambda item: str(item[2])
                )
        else:
            if split_start_groups:
                self.person_array = sorted(
                    self.person_array, key=lambda item: str(item[1]) + str(item[2])
                )
            else:
                self.person_array = sorted(
                    self.person_array, key=lambda item: str(item[1])
                )

        # process team and region conflicts in each start group
        self.process_conflicts()

        # apply to initial list
        return self.get_tossed_array(persons)

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
                        print('no solution found for group ' + self.person_array[j][1])
                        return False
                    else:
                        # insert j after checked_index i
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

    def process(
        self, mode='interval', first_number=None, interval=None, mix_groups=False
    ):
        if mode == 'interval':
            cur_num = first_number
            for cur_corridor in get_corridors():
                cur_num = self.process_corridor_by_order(
                    cur_corridor, cur_num, interval
                )
        else:
            first_number = 1
            cur_num = first_number
            for cur_corridor in get_corridors():
                if mode == 'corridor_minute':
                    cur_num = self.process_corridor_by_minute(cur_corridor, cur_num)
                elif mode == 'corridor_order':
                    cur_num = self.process_corridor_by_order(cur_corridor, cur_num)
                cur_num = cur_num - (cur_num % 100) + 101

    def process_corridor_by_order(self, corridor, first_number=1, interval=1):
        current_race = self.race
        persons = current_race.get_persons_by_corridor(
            corridor
        )  # get persons of current corridor
        # persons = sorted(persons, key=lambda item: item.start_time)  # sort by start time
        return self.set_numbers_by_order(persons, first_number, interval)

    def process_corridor_by_minute(self, corridor, first_number=1):
        current_race = self.race
        persons = current_race.get_persons_by_corridor(corridor)
        return self.set_numbers_by_minute(persons, first_number)

    def set_numbers_by_minute(self, persons, first_number=1):
        max_assigned_num = first_number
        if persons and len(persons) > 0:

            # first find minimal start time
            first_start = min(persons, key=lambda x: x.start_time).start_time
            if not first_start:
                first_start = OTime()

            # find number >= initial first number and have %100 = first start minute
            minute = first_start.minute
            min_num = int(first_number / 100) * 100 + minute
            if min_num < first_number:
                min_num += 100

            for current_person in persons:
                if current_person.start_time:
                    start_time = current_person.start_time
                    delta = (start_time - first_start).to_minute()
                    current_person.bib = int(min_num + delta)
                    max_assigned_num = max(max_assigned_num, current_person.bib)
                else:
                    current_person.bib = 0

        if max_assigned_num > first_number:
            return max_assigned_num + 1
        return first_number

    def set_numbers_by_order(self, persons, first_number=1, interval=1):
        cur_number = first_number
        if persons and len(persons) > 0:
            for current_person in persons:
                current_person.bib = cur_number
                cur_number += interval
        return cur_number


class StartTimeManager(object):
    def __init__(self, r):
        self.race = r

    """
        Set new start time for athletes

    """

    def process(
        self,
        corridor_first_start,
        is_group_start_interval,
        fixed_start_interval=None,
        one_minute_qty=1,
        mix_groups=False,
    ):
        current_race = self.race
        current_race.update_counters()

        corridors = get_corridors()
        for cur_corridor in corridors:
            cur_start = corridor_first_start

            if mix_groups:
                self.process_corridor(
                    cur_corridor, cur_start, fixed_start_interval, one_minute_qty
                )
            else:
                groups = get_groups_by_corridor(cur_corridor)
                for cur_group in groups:
                    start_interval = fixed_start_interval

                    # try to take start interval from group properties
                    if is_group_start_interval:
                        if cur_group.start_interval:
                            start_interval = cur_group.start_interval

                    cur_start = self.process_group(
                        cur_group, cur_start, start_interval, one_minute_qty
                    )

    def process_group(self, group, first_start, start_interval, one_minute_qty):
        current_race = self.race
        persons = current_race.get_persons_by_group(group)
        current_start = first_start
        one_minute_count = 0
        if persons:
            for current_person in persons:
                current_person.start_time = current_start
                one_minute_count += 1
                if one_minute_count >= one_minute_qty:
                    current_start = current_start + start_interval
                    one_minute_count = 0

        if one_minute_count > 0:
            current_start = current_start + start_interval
        return current_start

    def process_corridor(self, corridor, first_start, start_interval, one_minute_qty):
        current_race = self.race
        persons = current_race.get_persons_by_corridor(corridor)
        if persons:
            current_start = first_start
            one_minute_count = 0
            for current_person in persons:
                current_person.start_time = current_start
                one_minute_count += 1
                if one_minute_count >= one_minute_qty:
                    current_start = current_start + start_interval
                    one_minute_count = 0


def get_corridors():
    current_race = race()
    ret = []
    for current_group in current_race.groups:
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
        cur_corridor = current_group.start_corridor
        if not cur_corridor:
            cur_corridor = 0
        if cur_corridor == corridor:
            ret.append(current_group)
    return sorted(ret, key=lambda item: item.order_in_corridor)


def guess_courses_for_groups():
    obj = race()
    for cur_group in obj.groups:
        if not cur_group.course or True:  # TODO check empty courses after export!
            for cur_course in obj.courses:
                course_name = cur_course.name
                group_name = cur_group.name
                if str(course_name).find(group_name) > -1:
                    cur_group.course = cur_course
                    logging.debug(
                        'Connecting: group '
                        + group_name
                        + ' with course '
                        + course_name
                    )
                    break


def guess_corridors_for_groups():
    obj = race()
    course_index = 1
    for cur_course in obj.courses:
        cur_course.corridor = course_index
        course_index += 1

    for cur_group in obj.groups:
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


def handicap_start_time():
    obj = race()
    handicap_start = OTime(
        msec=obj.get_setting('handicap_start', OTime(hour=11).to_msec())
    )
    handicap_max_gap = OTime(
        msec=obj.get_setting('handicap_max_gap', OTime(minute=30).to_msec())
    )
    handicap_second_start = OTime(
        msec=obj.get_setting(
            'handicap_second_start', OTime(hour=11, minute=30).to_msec()
        )
    )
    handicap_interval = OTime(
        msec=obj.get_setting('handicap_interval', OTime(minute=30).to_msec())
    )

    rc = ResultCalculation(obj)
    for group in obj.groups:
        results = rc.get_group_finishes(group)  # get sorted results
        leader_time = rc.get_group_leader_time(group)
        changed_persons = []

        current_second_group_time = handicap_second_start

        for result in results:
            cur_time = result.get_result_otime()
            gap = cur_time - leader_time

            if gap < handicap_max_gap and result.is_status_ok():
                start_time = handicap_start + gap
            else:
                start_time = current_second_group_time
                current_second_group_time += handicap_interval

            if result.person:
                result.person.start_time = start_time
                changed_persons.append(result.person)

        # also process people without finish (DNS)
        persons = rc.get_group_persons(group)
        for person in persons:
            if person not in changed_persons:
                person.start_time = current_second_group_time
                current_second_group_time += handicap_interval


def reverse_start_time():
    obj = race()
    handicap_start = OTime(
        msec=obj.get_setting('handicap_start', OTime(hour=11).to_msec())
    )
    handicap_interval = OTime(
        msec=obj.get_setting('handicap_interval', OTime(minute=30).to_msec())
    )
    handicap_dsg_offset = OTime(
        msec=obj.get_setting('handicap_dsg_offset', OTime(minute=10).to_msec())
    )

    rc = ResultCalculation(obj)
    for group in obj.groups:
        results = rc.get_group_finishes(group)  # get sorted results
        first_group = []
        second_group = []

        for result in results:
            if result.is_status_ok() and result.person:
                second_group.append(result.person)

        # reverse main group, leader should be last
        second_group.reverse()

        persons = rc.get_group_persons(group)
        for person in persons:
            if person not in second_group:
                first_group.append(person)

        # first process DSQ and DNS - toss them
        first_group = DrawManager(obj).process_array(first_group, False, True, False)

        cur_time = handicap_start
        for person in first_group:
            person.start_time = cur_time
            cur_time += handicap_interval

        # add offset after DSQ and DNS
        cur_time += handicap_dsg_offset - handicap_interval

        # set time for main group
        for person in second_group:
            person.start_time = cur_time
            cur_time += handicap_interval


def copy_bib_to_card_number():
    obj = race()
    for person in obj.persons:
        if person.bib:
            person.card_number = person.bib


def copy_card_number_to_bib():
    obj = race()
    for person in obj.persons:
        if person.card_number:
            person.bib = person.card_number


def clone_relay_legs(min_bib, max_bib, increment):
    """Clone existing relay legs to new (the same names, bib += increment"""
    if min_bib + increment < max_bib:
        return

    obj = race()
    for person in obj.persons:
        if person.bib and person.bib >= min_bib and person.bib <= max_bib:
            new_person = copy(person)
            new_person.id = uuid.uuid4()
            new_person.bib = person.bib + increment
            new_person.card_number = 0
            obj.persons.append(new_person)
