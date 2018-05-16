from sportorg.models.memory import Course, Group, Qualification, ResultStatus
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.utils.time import get_speed_min_per_km


class PersonSplits(object):
    def __init__(self, r, result):

        self.race = r
        self.result = result
        self._course = None

        self.assigned_rank = ''
        if hasattr(self.result, 'assigned_rank') and self.result.assigned_rank != Qualification.NOT_QUALIFIED:
            self.assigned_rank = self.result.assigned_rank.get_title()

        self.relay_leg = self.result.person.bib // 1000
        self.last_correct_index = 0

    @property
    def person(self):
        return self.result.person

    @property
    def course(self):
        if self._course is None:
            self._course = self.race.find_course(self.person)
            if self._course is None:
                self._course = Course()
        return self._course

    def generate(self):
        split_index = 0
        course_index = 0
        course_code = 0
        if len(self.course.controls) > course_index:
            course_code = self.course.controls[course_index].code
        leg_start_time = self.result.get_start_time()
        start_time = self.result.get_start_time()

        if self.course.length:
            self.result.speed = get_speed_min_per_km(self.result.get_result_otime(), self.course.length)

        while split_index < len(self.result.splits):
            cur_split = self.result.splits[split_index]

            cur_split.index = split_index
            cur_split.relative_time = cur_split.time - start_time

            if course_code == cur_split.code:
                cur_split.leg_time = cur_split.time - leg_start_time
                leg_start_time = cur_split.time

                cur_split.course_index = course_index
                cur_split.length_leg = self.course.controls[course_index].length
                if cur_split.length_leg:
                    cur_split.speed = get_speed_min_per_km(cur_split.leg_time, cur_split.length_leg)

                cur_split.leg_place = 0

                course_index += 1
                if course_index >= len(self.course.controls):
                    course_code = -1
                else:
                    course_code = self.course.controls[course_index].code

            else:
                cur_split.is_correct = False

            split_index += 1

        self.last_correct_index = course_index - 1
        return self

    def get_last_correct_index(self):
        return self.last_correct_index

    def get_leg_by_course_index(self, index):
        if index > self.get_last_correct_index():
            return None

        for i in self.result.splits:
            if i.course_index == index:
                return i

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
            'person': self.person.to_dict(),
            'result': self.result.to_dict(),
            'course': self.course.to_dict()
        }


class GroupSplits(object):
    def __init__(self, r, group):
        self.race = r
        assert isinstance(group, Group)
        self.group = group
        self.cp_count = len(self.group.course.controls) if self.group.course else 0

        self.person_splits = []

        self.leader = {}

    def generate(self):
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
        len_persons = len(self.person_splits)
        for i in range(self.cp_count):
            self.sort_by_leg(i)
            self.set_places_for_leg(i)
            if not len_persons > 0:
                continue
            self.set_leg_leader(i, self.person_splits[0])

            self.sort_by_leg(i, relative=True)
            self.set_places_for_leg(i, relative=True)

    def sort_by_leg(self, index, relative=False):
        if relative:
            self.person_splits = sorted(
                self.person_splits,
                key=lambda item: (item.get_leg_relative_time(index) is None, item.get_leg_relative_time(index))
            )
        else:
            self.person_splits = sorted(
                self.person_splits,
                key=lambda item: (item.get_leg_time(index) is None, item.get_leg_time(index))
            )

    def sort_by_result(self):
        status_priority = [
            ResultStatus.OVERTIME.value,
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
                item.result.get_place() is None or item.result.get_place() == '',
                ('0000' + str(item.result.get_place()))[-4:],
                int(item.relay_leg)
            )
        )

    def set_places_for_leg(self, index, relative=False):
        if not len(self.person_splits):
            return

        leader = self.person_splits[0].result.person
        leader_time = self.person_splits[0].get_leg_time(index)

        for i in range(len(self.person_splits)):
            person = self.person_splits[i]
            leg = person.get_leg_by_course_index(index)
            if leg:
                if relative:
                    leg.relative_place = i + 1
                else:
                    leg.leg_place = i + 1
                    leg.leader = leader
                    leg.leader_time = leader_time

    def set_leg_leader(self, index, person_split):
        self.leader[str(index)] = (person_split.person.name, person_split.get_leg_time(index))

    def get_leg_leader(self, index):
        if str(index) in self.leader.keys():
            return self.leader[str(index)]
        return '', ''

    def set_places_relative(self):
        for i in range(self.cp_count):
            self.sort_by_leg(i, True)
            self.set_places_for_leg(i, True)

    def to_dict(self):
        return [ps.to_dict() for ps in self.person_splits]


class RaceSplits(object):
    def __init__(self, r):
        self.race = r

    def generate(self):
        for group in self.race.groups:
            GroupSplits(self.race, group).generate()
        return self
