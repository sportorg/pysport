import logging
import math
import uuid
from copy import copy
from random import randint, shuffle
from typing import Dict, List

from sportorg.common.otime import OTime
from sportorg.models.memory import Person, race
from sportorg.models.result.result_calculation import ResultCalculation


class ReserveManager:
    """Inserts reserve athletes into each group.

    You can specify minimum quantity of person or percentage to add in each group.
    Reserve record is marked with prefix, that can be specified by user.

    Now effect on all groups, but in future we'll possible implement working
    with selected groups only.
    """

    def __init__(self, r):
        self.race = r

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
                        "" + str(current_person.surname) + str(current_person.name)
                    )
                    if str.find(str_name, reserve_prefix) > -1:
                        existing_reserves += 1

            insert_count = int(max(reserve_count, percent_count) - existing_reserves)

            for i in range(insert_count):
                new_person = Person()
                new_person.surname = reserve_prefix
                new_person.group = current_group
                current_race.add_person(new_person)


class DrawManager:
    """Execute draw in each group.

    Now effect on all groups, but in future we'll possibly implement working
    with filtered persons.
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
            group = ""
            if current_person.group:
                group = current_person.group.name
            start_group = current_person.start_group
            team = ""
            region = ""
            if current_person.organization:
                team = current_person.organization.name
                region = current_person.organization.region

            self.person_array.append(
                [index, group, "{:03}".format(start_group), team, region]
            )

    def get_tossed_array(self, persons):
        index_array = []
        for i in self.person_array:
            index_array.append(i[0])
        ret = [persons[x] for x in index_array]
        return ret

    def process(self, split_start_groups, split_teams, split_regions, mix_groups=False):
        current_race = self.race
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
        obj = race()
        person_array = []

        # toss by course
        if mix_groups:
            for cur_course in obj.courses + [None]:
                groups = []
                for cur_group in obj.groups:
                    if cur_group.course == cur_course:
                        groups.append(cur_group)

                if len(groups) < 1:
                    continue

                cur_array = []
                for cur_person in persons:
                    assert isinstance(cur_person, Person)
                    if cur_person.group in groups:
                        cur_array.append(cur_person)

                if len(cur_array) < 1:
                    continue

                person_array += self.process_array_start_group(
                    cur_array, split_start_groups, split_teams, split_regions
                )

        # toss by group
        else:
            cur_group = None
            cur_array = []
            # sort all person by group
            for cur_person in sorted(
                persons, key=lambda x: x.group.name if x.group else ""
            ):
                if not cur_group:
                    cur_group = cur_person.group
                if cur_person.group != cur_group:
                    # if group in sorted list changed, process current sub list
                    person_array += self.process_array_start_group(
                        cur_array, split_start_groups, split_teams, split_regions
                    )
                    cur_array = []
                    cur_group = cur_person.group
                cur_array.append(cur_person)

            # last part outside loop
            person_array += self.process_array_start_group(
                cur_array, split_start_groups, split_teams, split_regions
            )

        return person_array

    def process_array_start_group(
        self, persons, split_start_groups: bool, split_teams: bool, split_regions: bool
    ):
        if split_start_groups:
            # split by start group, toss each group and then process conflicts on the boundaries
            cur_start_group = -1
            persons_sub_lists = []
            cur_array: List[Person] = []
            for cur_person in sorted(persons, key=lambda x: x.start_group):
                if cur_start_group < 0:
                    cur_start_group = cur_person.start_group
                if cur_person.start_group != cur_start_group:
                    # if start group in sorted list changed, process current sub list
                    persons_sub_lists.append(
                        self.process_array_impl(cur_array, split_teams, split_regions)
                    )
                    cur_array = []
                    cur_start_group = cur_person.start_group
                cur_array.append(cur_person)

            persons_sub_lists.append(
                self.process_array_impl(cur_array, split_teams, split_regions)
            )

            ret_array: List[int] = []
            conflict_list: List[int] = []
            for i in range(len(persons_sub_lists) - 1):
                # first find any start group, that cannot be changed (max set >= (N+1)//2)
                cur_list = persons_sub_lists[i]
                next_list = persons_sub_lists[i + 1]

                cur_prop = self.get_split_property(
                    cur_list[-1], split_teams, split_regions
                )
                next_prop = self.get_split_property(
                    next_list[0], split_teams, split_regions
                )
                if cur_prop == next_prop:
                    # conflict detected
                    conflict_list.append(i)

            if len(conflict_list) > 0:
                # conflict on boundaries found, try to process

                fixed_list: List[int] = []
                incorrect_list: List[int] = []
                self.detect_fixed_sets(
                    persons_sub_lists,
                    incorrect_list,
                    fixed_list,
                    split_teams,
                    split_regions,
                )

                while len(conflict_list) > 0:
                    i = conflict_list.pop(0)
                    if i in fixed_list and i + 1 in fixed_list:
                        # 2 sets are fixed or incorrect, cannot solve conflict
                        # e.g. A,B,A and A,D,A,C,A
                        logging.info(
                            f"conflict on start group boundaries cannot be solved!"
                            f" group: {persons_sub_lists[i][0].group.name},"
                            f" start groups: {persons_sub_lists[i][0].start_group},"
                            f" {persons_sub_lists[i + 1][0].start_group}"
                        )
                        break

                    if i + 1 not in fixed_list:
                        self.direct_solving(
                            persons_sub_lists,
                            conflict_list,
                            fixed_list,
                            i,
                            split_teams,
                            split_regions,
                        )
                    elif i not in fixed_list:
                        self.backward_solving(
                            persons_sub_lists,
                            conflict_list,
                            fixed_list,
                            i,
                            split_teams,
                            split_regions,
                        )

            for i in range(len(persons_sub_lists)):
                ret_array += persons_sub_lists[i]

            return ret_array
        else:
            return self.process_array_impl(persons, split_teams, split_regions)

    def detect_fixed_sets(
        self, persons_sub_lists, incorrect_list, fixed_list, split_teams, split_regions
    ):
        for i in range(len(persons_sub_lists)):
            cur_list = persons_sub_lists[i]

            is_fixed = False
            is_correct = True

            # check for correctness, neighbours should be different
            for j in range(len(cur_list) - 1):
                prop1 = self.get_split_property(cur_list[j], split_teams, split_regions)
                prop2 = self.get_split_property(
                    cur_list[j + 1], split_teams, split_regions
                )
                if prop1 == prop2:
                    is_correct = False
                    break

            # find fixed sets, that cannot change boundary elements
            # (odd and each second is the same, e.g. A,B,A,C,A,D,A,F,A)
            if is_correct and len(cur_list) % 2 == 1:
                is_fixed = True
                check_name = self.get_split_property(
                    cur_list[0], split_teams, split_regions
                )
                for j in range(len(cur_list)):
                    if j % 2 == 0:
                        if (
                            self.get_split_property(
                                cur_list[j], split_teams, split_regions
                            )
                            != check_name
                        ):
                            is_fixed = False
                            break

            if is_correct:
                if is_fixed:
                    fixed_list.append(i)
            else:
                incorrect_list.append(i)
                fixed_list.append(i)

    def direct_solving(
        self,
        persons_sub_lists,
        conflict_list,
        fixed_list,
        i,
        split_teams,
        split_regions,
    ) -> bool:
        # forward moving, till all conflicts are solved of fixed list meet

        if i >= len(persons_sub_lists) - 1:
            # last element reached, solved successfully
            return True

        if i + 1 in fixed_list:
            # fixed set found, cannot solve, register conflict for backward solution
            if i not in conflict_list:
                conflict_list.append(i)
            return False

        person1 = persons_sub_lists[i][-1]
        person2 = persons_sub_lists[i + 1][0]
        prop1 = self.get_split_property(person1, split_teams, split_regions)
        prop2 = self.get_split_property(person2, split_teams, split_regions)
        if prop1 != prop2:
            # solved at current position
            return True

        if i in conflict_list:
            # remove from conflict list not to check again
            conflict_list.remove(i)

        if self.change_first(persons_sub_lists[i + 1], split_teams, split_regions):
            # first element changed and conflict solved
            return True

        # recursive call for semi-fixed sets
        return self.direct_solving(
            persons_sub_lists,
            conflict_list,
            fixed_list,
            i + 1,
            split_teams,
            split_regions,
        )

    def backward_solving(
        self,
        persons_sub_lists,
        conflict_list,
        fixed_list,
        i,
        split_teams,
        split_regions,
    ) -> bool:
        # backward moving, till all conflicts are changed of fixed list meet
        # note, it's activated only if direct solving is not possible

        if i < 0:
            # first element, solved successfully
            return True

        if i in fixed_list:
            # cannot solve - 2 fixed sets connected with semi-fixed sets
            logging.info(
                f"conflict on start group boundaries cannot be solved!"
                f"2 fixed sets connected with semi-fixed sets"
                f" group: {persons_sub_lists[i][0].group.name},"
                f" start groups: {persons_sub_lists[i][0].start_group},"
                f" {persons_sub_lists[i + 1][0].start_group}"
            )
            return False

        person1 = persons_sub_lists[i][-1]
        person2 = persons_sub_lists[i + 1][0]
        prop1 = self.get_split_property(person1, split_teams, split_regions)
        prop2 = self.get_split_property(person2, split_teams, split_regions)
        if prop1 != prop2:
            # solved at current position
            return True

        if self.change_last(persons_sub_lists[i], split_teams, split_regions):
            # last element changed and conflict solved
            return True

        # recursive call for semi-fixed sets
        return self.backward_solving(
            persons_sub_lists,
            conflict_list,
            fixed_list,
            i - 1,
            split_teams,
            split_regions,
        )

    def change_last(self, persons, split_teams, split_regions) -> bool:
        # returns True if last element changed and first remain the same
        # returns False if changing of last element forced first element change (A,B -> B,A)

        last_prop = self.get_split_property(persons[-1], split_teams, split_regions)
        for i in range(len(persons) - 1):
            prop1 = self.get_split_property(persons[i], split_teams, split_regions)
            prop2 = self.get_split_property(persons[i + 1], split_teams, split_regions)
            if prop1 != last_prop and prop2 != last_prop:
                person = persons.pop(-1)
                persons.insert(i + 1, person)
                logging.info(
                    f"Conflict at start group boundaries solving in group: {person.group.name}, "
                    f"moving {person.full_name} to position {i + 2}"
                )
                return True

        # had to change first element, e.g. A,B,A,B -> B,A,B,A
        # dangerous operation, need to check for conflicts again
        if last_prop != self.get_split_property(persons[0], split_teams, split_regions):
            persons.insert(0, persons.pop(-1))
            return False

        # cannot change last element
        logging.debug("Cannot change last element, send file to developers!")
        return False

    def change_first(self, persons, split_teams, split_regions):
        persons.reverse()
        self.change_last(persons, split_teams, split_regions)
        persons.reverse()

    def process_array_impl(self, persons, split_teams: bool, split_regions: bool):
        shuffle(persons)
        separated_dict: Dict[str, List[Person]] = {}
        result_list: List[Person] = []

        # separate all person to arrays by split property
        for cur_person in persons:
            prop = self.get_split_property(cur_person, split_teams, split_regions)
            if prop not in separated_dict:
                separated_dict[prop] = []
            separated_dict[prop].append(cur_person)

        rest_count = len(persons)
        max_name, max_count, max_index = self.get_max_group_size(separated_dict, "")
        duplicated_array: List[Person] = []

        # limit = (N+1)//2 (e.g. 5 for 10 and 6 for 11)
        limit = (rest_count + 1) // 2
        if max_count > limit:
            # impossible to split
            duplicated_array = separated_dict[max_name][limit:]
            separated_dict[max_name] = separated_dict[max_name][:limit]
            rest_count -= len(duplicated_array)

        cur_index = 0
        cur_prop = ""
        while max_count > 0:
            limit = (rest_count + 1) // 2
            if max_count >= limit:
                # take person from max set, otherwise they will be duplicated
                cur_prop = max_name
                cur_index = max_index
            else:
                # can take person from random set
                # add one index of list for each element of list to have proportional shuffle
                shuffle_indexes = []
                for i in range(len(separated_dict)):
                    if cur_index == i:
                        continue  # skip previous value not to duplicate
                    i_prop = list(separated_dict.keys())[i]
                    for j in range(len(separated_dict[i_prop])):
                        shuffle_indexes.append(i)
                cur_index = shuffle_indexes[randint(0, len(shuffle_indexes) - 1)]
                cur_prop = list(separated_dict.keys())[cur_index]

            # extract person from selected set
            result_list.append(separated_dict[cur_prop].pop(0))
            rest_count -= 1
            if len(separated_dict[cur_prop]) < 1:
                # remove set if it's empty
                separated_dict.pop(cur_prop)

            # recalculate max set for next loop
            max_name, max_count, max_index = self.get_max_group_size(
                separated_dict, cur_prop
            )

        # insert at random positions rest values, that are out of limit N/2 for max set
        if len(duplicated_array) > 0:
            for cur_person in duplicated_array:
                result_list.insert(randint(0, len(result_list) - 1), cur_person)
        if cur_prop in separated_dict.keys():
            array_tmp = separated_dict.get(cur_prop)
            if array_tmp:
                for cur_person in array_tmp:
                    pos = 0
                    if len(result_list) > 1:
                        pos = randint(0, len(result_list) - 1)
                    result_list.insert(pos, cur_person)

        return result_list

    def get_split_property(self, person, split_teams, split_regions) -> str:
        if person.organization is None:
            return "s"

        if split_regions:
            return person.organization.region
        elif split_teams:
            return person.organization.name
        else:
            return "s"

    def get_max_group_size(self, separated_dict: dict, ignore_name):
        max_count = 0
        max_index = 0
        max_group = None
        i = -1
        for k in separated_dict.keys():
            i += 1
            if ignore_name == k:
                continue
            if len(separated_dict[k]) > max_count:
                max_count = len(separated_dict[k])
                max_group = k
                max_index = i

        return max_group, max_count, max_index


class StartNumberManager:
    """Assign new start numbers."""

    def __init__(self, r):
        self.race = r

    def process(
        self, mode="interval", first_number=None, interval=None, mix_groups=False
    ):
        if mode == "interval":
            cur_num = first_number
            for cur_corridor in get_corridors():
                cur_num = self.process_corridor_by_order(
                    cur_corridor, cur_num, interval
                )
        else:
            first_number = 1
            cur_num = first_number
            for cur_corridor in get_corridors():
                if mode == "corridor_minute":
                    cur_num = self.process_corridor_by_minute(cur_corridor, cur_num)
                elif mode == "corridor_order":
                    cur_num = self.process_corridor_by_order(cur_corridor, cur_num)
                cur_num = cur_num - (cur_num % 100) + 101

    def process_corridor_by_order(self, corridor, first_number=1, interval=1):
        current_race = self.race
        # get persons of current corridor
        persons = current_race.get_persons_by_corridor(corridor)
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
                    current_person.set_bib(int(min_num + delta))
                    max_assigned_num = max(max_assigned_num, current_person.bib)
                else:
                    current_person.set_bib(0)

        if max_assigned_num > first_number:
            return max_assigned_num + 1
        return first_number

    def set_numbers_by_order(self, persons, first_number=1, interval=1):
        cur_number = first_number
        if persons and len(persons) > 0:
            for current_person in persons:
                current_person.set_bib(cur_number)
                cur_number += interval
        return cur_number


class StartTimeManager:
    """Set new start time for athletes."""

    def __init__(self, r):
        self.race = r

    def process(
        self,
        corridor_first_start,
        is_group_start_interval,
        fixed_start_interval=None,
        one_minute_qty=1,
        mix_groups=False,
    ):
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
                        "Connecting: group "
                        + group_name
                        + " with course "
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
        msec=obj.get_setting("handicap_start", OTime(hour=11).to_msec())
    )
    handicap_max_gap = OTime(
        msec=obj.get_setting("handicap_max_gap", OTime(minute=30).to_msec())
    )
    handicap_second_start = OTime(
        msec=obj.get_setting(
            "handicap_second_start", OTime(hour=11, minute=30).to_msec()
        )
    )
    handicap_interval = OTime(
        msec=obj.get_setting("handicap_interval", OTime(minute=30).to_msec())
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
        msec=obj.get_setting("handicap_start", OTime(hour=11).to_msec())
    )
    handicap_interval = OTime(
        msec=obj.get_setting("handicap_interval", OTime(minute=30).to_msec())
    )
    handicap_dsq_offset = OTime(
        msec=obj.get_setting("handicap_dsq_offset", OTime(minute=10).to_msec())
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
        cur_time += handicap_dsq_offset - handicap_interval

        # set time for main group
        for person in second_group:
            person.start_time = cur_time
            cur_time += handicap_interval


def copy_bib_to_card_number():
    obj = race()
    for person in obj.persons:
        if person.bib:
            person.set_card_number(person.bib)


def copy_card_number_to_bib():
    obj = race()
    for person in obj.persons:
        if person.card_number:
            person.set_bib(person.card_number)


def clone_relay_legs(min_bib, max_bib, increment):
    """Clone existing relay legs to new (the same names, bib += increment"""
    if min_bib + increment < max_bib:
        return

    obj = race()
    for person in obj.persons:
        if person.bib and min_bib <= person.bib <= max_bib:
            new_person = copy(person)
            new_person.id = uuid.uuid4()
            new_person.set_bib(person.bib + increment)
            new_person.set_card_number(0)
            obj.persons.append(new_person)
