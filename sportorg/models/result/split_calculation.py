from datetime import datetime

from sportorg.models.memory import race, Person, Course, Group, Qualification
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.utils.time import time_to_hhmmss, get_speed_min_per_km, if_none, hhmmss_to_time


class LegSplit(object):
    def __init__(self):
        self.index = 0
        self.course_index = -1
        self.code = 0
        self.absolute_time = None
        self.leg_time = None
        self.leg_minute_time = None
        self.relative_time = None
        self.leg_place = 0
        self.relative_place = 0
        self.status = 'correct'
        self.speed = ''
        self.length_leg = 0

    def get_json(self):
        ret = {
            'index': self.index,
            'course_index': self.course_index + 1,
            'code': self.code,
            'absolute_time': self.absolute_time,
            'relative_time': self.relative_time,
            'leg_time': self.leg_time,
            'leg_minute_time': self.leg_minute_time,
            'leg_place': self.leg_place,
            'relative_place': self.relative_place,
            'status': self.status,
            'speed': self.speed,
            'length_leg': self.length_leg
        }
        return ret


class PersonSplits(object):
    def __init__(self, result):

        person = result.person
        assert isinstance(person, Person)
        group = person.group
        course = group.course
        assert isinstance(course, Course)

        self.person = person

        self.legs = []

        self.name = person.full_name
        self.group = person.group.name
        self.bib = person.bib
        self.team = ''
        if person.organization:
            self.team = person.organization.name
        self.sportident_card = person.sportident_card
        self.qual = ''
        if person.qual:
            self.qual = person.qual.get_title()
        self.year = person.year

        race_result = result.get_finish_time() - result.get_start_time()

        self.start = time_to_hhmmss(person.start_time)
        self.finish = time_to_hhmmss(result.get_finish_time())
        self.result = result.get_result()
        self.splits = result.splits
        self.race_result = time_to_hhmmss(race_result)
        self.status = result.status.value
        self.status_title = result.status.get_title()
        self.place = result.place
        self.group_count_all = person.group.get_count_all()
        self.group_count_finished = person.group.get_count_finished()
        self.speed = ''
        if course.length:
            self.speed = get_speed_min_per_km(race_result, course.length)

        self.penalty_time = time_to_hhmmss(result.get_penalty_time())

        if result.assigned_rank == Qualification.NOT_QUALIFIED:
            self.assigned_rank = ''
        else:
            self.assigned_rank = result.assigned_rank.get_title()

        person_index = 0
        course_index = 0
        course_code = 0
        if len(course.controls) > course_index:
            course_code = course.controls[course_index].code
            if str(course_code).strip().isdigit():
                course_code = int(str(course_code).strip())
        leg_start_time = result.get_start_time()
        start_time = result.get_start_time()

        while person_index < len(result.splits):
            cur_split = result.splits[person_index]
            cur_code = cur_split.code
            cur_time = cur_split.time

            leg = LegSplit()
            leg.code = cur_code
            leg.index = person_index
            leg.absolute_time = time_to_hhmmss(cur_time)
            leg.relative_time = time_to_hhmmss(cur_time - start_time)

            leg.status = 'correct'
            if course_code == cur_code:
                leg_time = cur_time - leg_start_time
                leg.leg_time = time_to_hhmmss(leg_time)
                leg.leg_minute_time = leg_time.to_minute_str()
                leg_start_time = cur_time

                leg.course_index = course_index
                leg.length_leg = course.controls[course_index].length
                if leg.length_leg:
                    leg.speed = get_speed_min_per_km(leg_time, leg.length_leg)

                leg.leg_place = '0'

                course_index += 1
                if course_index >= len(course.controls):
                    course_code = -1
                else:
                    course_code = course.controls[course_index].code
                    if str(course_code).strip().isdigit():
                        course_code = int(str(course_code).strip())

            else:
                leg.status = 'extra'

            self.legs.append(leg)

            person_index += 1

        self.last_correct_index = course_index - 1

    def get_last_correct_index(self):
        return self.last_correct_index

    def get_leg_by_course_index(self, index):
        if index > self.get_last_correct_index():
            return None

        for i in self.legs:
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

    def get_person_split_data(self):
        ret = {
            'name': self.name,
            'team': self.team,
            'qual': self.qual,
            'year': self.year,
            'bib': self.bib if self.bib else '',
            'result': self.result,
            'penalty_time': self.penalty_time,
            'place': self.place,
            'assigned_rank': if_none(self.assigned_rank, ''),
            'legs': [],
            'splits': []
        }

        for split in self.splits:
            ret['splits'].append({
                'code': split.code,
                'time': str(split.time)
            })

        for i in self.legs:
            assert isinstance(i, LegSplit)
            ret['legs'].append(i.get_json())

        return ret


class GroupSplits(object):
    def __init__(self, group):

        self.person_splits = []

        assert isinstance(group, Group)
        self.name = group.name
        self.cp_count = len(group.course.controls)
        self.length = group.course.length
        self.climb = group.course.climb
        self.controls = group.course.controls

        self.leader = {}

        # to have group count
        ResultCalculation().get_group_persons(group)
        self.count_all = group.get_count_all()

        self.count_finished = group.get_count_finished()

        for i in ResultCalculation().get_group_finishes(group):
            person = PersonSplits(i)
            self.person_splits.append(person)

        self.set_places()
        self.sort_by_result()

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
            self.person_splits = sorted(self.person_splits,
                                        key=lambda item: (item.get_leg_relative_time(index) is None,
                                                          item.get_leg_relative_time(index)))
        else:
            self.person_splits = sorted(self.person_splits,
                                        key=lambda item: (item.get_leg_time(index) is None,
                                                          item.get_leg_time(index)))

    def sort_by_result(self):
        self.person_splits = sorted(self.person_splits, key=lambda item: (item.result is None, item.result))

    def set_places_for_leg(self, index, relative=False):
        for i in range(len(self.person_splits)):
            person = self.person_splits[i]
            leg = person.get_leg_by_course_index(index)
            if leg:
                if relative:
                    leg.relative_place = i + 1
                else:
                    leg.leg_place = i + 1

    def set_leg_leader(self, index, person):
        self.leader[str(index)] = (person.name, person.get_leg_time(index))

    def get_leg_leader(self, index):
        if str(index) in self.leader.keys():
            return self.leader[str(index)]
        return '', ''

    def set_places_relative(self):
        for i in range(self.cp_count):
            self.sort_by_leg(i, True)
            self.set_places_for_leg(i, True)

    def get_json(self, person_to_export=None):
        ret = {}
        group_json = {}
        group_json['name'] = self.name
        group_json['climb'] = self.climb
        group_json['count_all'] = self.count_all
        group_json['count_finished'] = self.count_finished
        group_json['cp_count'] = self.cp_count
        group_json['controls'] = self.controls
        group_json['length'] = self.length
        persons = []
        for i in self.person_splits:
            assert (isinstance(i, PersonSplits))

            if person_to_export:
                if not person_to_export == i.person:
                    continue

            person_json = {}
            person_json['name'] = i.name
            person_json['bib'] = i.bib
            person_json['team'] = i.team
            person_json['sportident_card'] = int(i.sportident_card)
            person_json['last_correct_index'] = i.last_correct_index
            person_json['place'] = i.place
            person_json['start'] = i.start
            person_json['finish'] = i.finish
            person_json['result'] = i.result
            person_json['race_result'] = i.race_result
            person_json['speed'] = i.speed
            person_json['status'] = i.status
            person_json['status_title'] = i.status_title
            person_json['penalty_time'] = i.penalty_time
            legs = []
            last_time = None
            for j in i.legs:
                assert (isinstance(j, LegSplit))
                leg_json = j.get_json()
                if j.course_index + 1:
                    leg_json['leader_name'] = self.get_leg_leader(j.course_index)[0]
                    leg_json['leader_time'] = self.get_leg_leader(j.course_index)[1]
                    last_time = hhmmss_to_time(leg_json['absolute_time'])

                legs.append(leg_json)

            person_json['legs'] = legs
            finish = hhmmss_to_time(i.finish)
            if last_time is not None and last_time != finish:
                person_json['finish_time'] = (finish - last_time).to_minute_str()
            else:
                person_json['finish_time'] = ''
            persons.append(person_json)

        group_json['persons'] = persons

        group_persons = []
        for i in self.person_splits:
            group_persons.append({
                'name': i.name,
                'bib': i.bib,
                'place': i.place,
                'result': i.result,
            })
        group_json['group_persons'] = group_persons

        groups = [group_json]
        ret['groups'] = groups

        start_date = race().get_setting('start_date', datetime.now().replace(second=0, microsecond=0))
        ret['race'] = {
            'title': race().get_setting('main_title', ''),
            'sub_title': race().get_setting('sub_title', ''),
            'location': race().get_setting('location', ''),
            'url': race().get_setting('url', ''),
            'date': start_date.strftime("%d.%m.%Y")
        }
        return ret


def get_splits_data():
    """

    :return: {
        "race": {"title": str, "sub_title": str},
        "groups": [
            {
                "name": str,
                "persons": [
                    PersonSplits.get_person_split_data,
                    ...
                ]
            }
        ]
    }
    """
    ret = {}
    data = []
    for group in race().groups:
        gs = GroupSplits(group)
        group_data = []
        mv = 0
        for res in gs.person_splits:
            assert isinstance(res, PersonSplits)
            person_data = res.get_person_split_data()
            group_data.append(person_data)
            mv = max(mv, len(person_data))

        ranking_data = group.ranking.get_json_data()

        data.append({
            'name': group.name,
            'persons': group_data,
            'ranking': ranking_data
        })
    data.sort(key=lambda x: x['name'])
    ret['groups'] = data
    start_date = race().get_setting('start_date', datetime.now().replace(second=0, microsecond=0))
    ret['race'] = {
        'title': race().get_setting('main_title', ''),
        'sub_title': race().get_setting('sub_title', ''),
        'url': race().get_setting('url', ''),
        'date': start_date.strftime("%d.%m.%Y")
    }
    return ret


class SplitsCalculation(object):
    @staticmethod
    def process_groups():
        for i in race().groups:
            GroupSplits(i)
