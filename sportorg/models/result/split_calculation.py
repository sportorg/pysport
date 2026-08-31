import logging
from typing import Optional

from sportorg.models.memory import Course, Group, Qualification, ResultStatus
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.utils.time import get_speed_min_per_km


class PersonSplits:
    def __init__(self, r, result):
        self.race = r
        self.result = result
        self._course = None
        self._legs = []

        self.assigned_rank = ""
        if (
            hasattr(self.result, "assigned_rank")
            and self.result.assigned_rank != Qualification.NOT_QUALIFIED
        ):
            self.assigned_rank = self.result.assigned_rank.get_title()

        self.relay_leg = self.result.person.bib // 1000
        self.last_correct_index = 0

    @property
    def person(self):
        return self.result.person

    @property
    def course(self):
        if self._course is None:
            self._course = self.race.find_course(self.result)
            if self._course is None:
                self._course = Course()
        return self._course

    def generate(self):
        split_index = 0
        course_index = 0
        leg_start_time = self.result.get_start_time()
        start_time = self.result.get_start_time()

        if self.course.length:
            self.result.speed = get_speed_min_per_km(
                self.result.get_result_otime(), self.course.length
            )

        for split in self.result.splits:
            split.relative_time = split.time - start_time

        if not len(self.course.controls):
            prev_split = start_time
            for i, split in enumerate(self.result.splits):
                split.index = i
                split.course_index = i
                split.leg_time = split.time - prev_split
                prev_split = split.time

        while split_index < len(self.result.splits) and course_index < len(
            self.course.controls
        ):
            cur_split = self.result.splits[split_index]

            cur_split.index = split_index

            if cur_split.is_correct:
                cur_split.leg_time = cur_split.time - leg_start_time
                leg_start_time = cur_split.time

                cur_split.course_index = course_index
                cur_split.length_leg = self.course.controls[course_index].length
                if cur_split.length_leg:
                    cur_split.speed = get_speed_min_per_km(
                        cur_split.leg_time, cur_split.length_leg
                    )

                cur_split.leg_place = 0

                course_index += 1
                self._legs.append(cur_split)

            split_index += 1

        self.last_correct_index = course_index - 1
        return self

    def get_last_correct_index(self):
        return self.last_correct_index

    def get_leg_by_course_index(self, index):
        if index > self.get_last_correct_index():
            return None

        if 0 <= index < len(self._legs):
            return self._legs[index]

        return None

    def get_leg_time(self, index):
        leg = self.get_leg_by_course_index(index)
        if leg:
            return leg.leg_time
        return None

    def get_leg_relative_time(self, index):
        leg = self.get_leg_by_course_index(index)
        if leg:
            return leg.relative_time
        return None

    def to_dict(self):
        return {
            "person": self.person.to_dict(),
            "result": self.result.to_dict(),
            "course": self.course.to_dict(),
        }


class GroupSplits:
    def __init__(self, r, group):
        self.race = r
        self.group = group
        self.cp_count = len(self.group.course.controls) if self.group.course else 0

        self.person_splits = []

        self.leader = {}

    def generate(self, logged=False):
        if logged:
            logging.debug("Group splits generate for " + self.group.name)
        # to have group count
        ResultCalculation(self.race).get_group_persons(self.group)

        for i in ResultCalculation(self.race).get_group_finishes(self.group):
            self.person_splits.append(PersonSplits(self.race, i).generate())

        self.set_places()
        if self.group.is_relay():
            self.sort_by_place()
        else:
            self.sort_by_result()
        return self

    def set_places(self):
        for index in range(self.cp_count):
            entries = []
            missing = []
            for person_split in self.person_splits:
                leg = person_split.get_leg_by_course_index(index)
                if leg is not None:
                    entries.append((person_split, leg))
                else:
                    missing.append(person_split)

            if not entries:
                continue

            entries.sort(key=lambda entry: entry[1].leg_time)
            self._assign_places(entries, "leg_time", "leg_place")
            self.set_leg_leader(index, entries[0][0])
            self.person_splits = [entry[0] for entry in entries] + missing

            entries.sort(key=lambda entry: entry[1].relative_time)
            self._assign_places(entries, "relative_time", "relative_place")
            self.person_splits = [entry[0] for entry in entries] + missing

    @staticmethod
    def _assign_places(entries, time_attr, place_attr):
        # competition ranking: equal times share a place, next place skips
        leader_time = getattr(entries[0][1], time_attr)
        double_places_counter = 0
        prev_time = leader_time
        for i, entry in enumerate(entries):
            leg = entry[1]
            leg_time = getattr(leg, time_attr)
            if i != 0 and prev_time == leg_time:
                double_places_counter += 1
            else:
                double_places_counter = 0

            setattr(leg, place_attr, i + 1 - double_places_counter)
            if place_attr == "leg_place":
                leg.leader_time = leader_time
            prev_time = leg_time

    def sort_by_result(self):
        status_priority = [
            ResultStatus.OVERTIME.value,
            ResultStatus.MISSING_PUNCH.value,
            ResultStatus.DISQUALIFIED.value,
            ResultStatus.DID_NOT_FINISH.value,
            ResultStatus.DID_NOT_START.value,
        ]

        def sort_func(item):
            priority = 0
            if item.result.status in status_priority:
                priority = status_priority.index(item.result.status) + 1
            return item.result is None, priority, item.result

        self.person_splits = sorted(self.person_splits, key=sort_func)

    def sort_by_place(self):
        self.person_splits = sorted(
            self.person_splits,
            key=lambda item: (
                item.result.get_place() is None or item.result.get_place() == "",
                ("0000" + str(item.result.get_place()))[-4:],
                int(item.relay_leg),
            ),
        )

    def set_leg_leader(self, index, person_split):
        self.leader[str(index)] = (
            person_split.person.name,
            person_split.get_leg_time(index),
        )

    def get_leg_leader(self, index):
        if str(index) in self.leader.keys():
            return self.leader[str(index)]
        return "", ""

    def to_dict(self):
        return [ps.to_dict() for ps in self.person_splits]


class RaceSplits:
    def __init__(self, r):
        self.race = r

    def generate(self, group: Optional[Group] = None):
        if group is None:
            for group in self.race.groups:
                GroupSplits(self.race, group).generate()
        else:
            GroupSplits(self.race, group).generate()

        return self
