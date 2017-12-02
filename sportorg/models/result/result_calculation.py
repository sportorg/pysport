from sportorg.core.otime import OTime
from sportorg.language import _
from sportorg.models.memory import race, Result, Person, ResultStatus, Course, Group, Qualification, RankingItem
from sportorg.utils.time import time_to_hhmmss


# FIXME: does not work sorting
class ResultCalculation(object):
    def process_results(self):
        self.set_times()
        for i in race().groups:
            array = self.get_group_finishes(i)
            self.set_places(array)
            self.set_rank(i)

    def set_times(self):
        for i in race().results:
            assert isinstance(i, Result)
            person = i.person
            if person and (i.start_time is None or (i.start_time is not None and i.start_time.to_sec() == 0)):
                i.start_time = person.start_time
            i.result = i.get_result_for_sort()

    def get_group_finishes(self, group):
        ret = []
        for i in race().results:
            assert isinstance(i, Result)
            person = i.person
            if person:
                assert isinstance(person, Person)
                if person.group == group:
                    ret.append(i)
        ret.sort()
        group.count_finished = len(ret)
        return ret

    def get_group_persons(self, group):
        assert isinstance(group, Group)
        ret = []
        for i in race().persons:
            person = i
            assert isinstance(person, Person)
            if person.group == group:
                ret.append(i)
        group.count_person = len(ret)
        return ret

    def set_places(self, array):
        assert isinstance(array, list)
        current_place = 1
        last_place = 1
        last_result = 0
        for i in range(len(array)):
            res = array[i]
            assert isinstance(res, Result)

            res.place = ''
            # give place only if status = OK
            if res.status == ResultStatus.OK:
                # skip if out of competition
                if res.person.is_out_of_competition:
                    res.place = _('o/c')
                    continue

                # the same place processing
                if current_place == 1 or res.result != last_result:
                    # result differs from previous - give next place
                    last_result = res.result
                    last_place = current_place

                res.place = last_place
                current_place += 1

    def set_rank(self, group):
        assert isinstance(group, Group)
        ranking = group.ranking
        results = self.get_group_finishes(group)

        # initial turning off, for disabling ranking
        for i in results:
            i.assigned_rank = Qualification.NOT_QUALIFIED

        if ranking.is_active:
            rank = self.get_group_rank(group)
            ranking.rank_scores = rank
            if rank > 0:
                leader_result = results[0]
                assert isinstance(leader_result, Result)
                leader_time = leader_result.get_result_otime()
                for i in ranking.rank.values():
                    assert isinstance(i, RankingItem)
                    if i.is_active and i.use_scores:
                        i.max_time = self.get_time_for_rank(leader_time, i.qual, rank)
                        i.percent = self.get_percent_for_rank(i.qual, rank)

            # Rank assigning for all athletes
            for i in results:
                assert isinstance(i, Result)
                result_time = i.get_result_otime()
                place = i.place

                if i.person.is_out_of_competition or i.status != ResultStatus.OK:
                    continue

                qual_list = sorted(ranking.rank.values(), reverse=True, key=lambda item: item.qual.get_scores())
                for j in qual_list:
                    assert isinstance(j, RankingItem)
                    if j.is_active:
                        if isinstance(place, int) and j.max_place >= place:
                            i.assigned_rank = j.qual
                            break
                        if j.max_time and j.max_time >= result_time:
                            i.assigned_rank = j.qual
                            break

    def get_group_rank(self, group):
        """
        Rank calculation, takes sums or scores from qualification of best 10 athletes, who have OK result and not o/c
        :param group:
        :return: rank of group, -1 if we have < 10 successfull results
        """
        scores = []
        for i in self.get_group_finishes(group):
            assert isinstance(i, Result)
            if i.status == ResultStatus.OK:
                person = i.person
                if not person.is_out_of_competition:
                    qual = person.qual
                    scores.append(qual.get_scores())
        if len(scores) < 10:
            return -1

        scores = sorted(scores)
        return sum(scores[-10:])

    def get_percent_for_rank(self, qual, rank):
        table = []
        if qual == Qualification.I:
            table = [
                 (1000, 136),
                 (850, 133),
                 (750, 130),
                 (650, 127),
                 (500, 124),
                 (425, 121),
                 (375, 118),
                 (325, 115),
                 (250, 112),
                 (211, 109),
                 (185, 106),
                 (159, 103),
                 (120, 100)
            ]
        elif qual == Qualification.II:
            table = [
                 (1000, 151),
                 (850, 148),
                 (750, 145),
                 (650, 142),
                 (500, 139),
                 (425, 136),
                 (375, 133),
                 (325, 130),
                 (250, 127),
                 (211, 124),
                 (185, 121),
                 (159, 118),
                 (120, 115),
                 (102, 112),
                 (90,  109),
                 (78,  106),
                 (60,  103),
                 (51,  100)
            ]
        elif qual == Qualification.III:
            table = [
                 (1000, 169),
                 (850, 166),
                 (750, 163),
                 (650, 160),
                 (500, 157),
                 (425, 154),
                 (375, 151),
                 (325, 148),
                 (250, 145),
                 (211, 142),
                 (185, 139),
                 (159, 136),
                 (120, 133),
                 (102, 130),
                 (90,  127),
                 (78,  124),
                 (60,  121),
                 (51,  118),
                 (45,  115),
                 (39,  112),
                 (30,  109),
                 (27,  106),
                 (25,  103),
                 (23,  100)
            ]
        elif qual == Qualification.I_Y:
            table = [
                 (250, 0),
                 (211, 172),
                 (185, 168),
                 (159, 164),
                 (120, 160),
                 (102, 156),
                 (90, 152),
                 (78, 148),
                 (60, 144),
                 (51, 140),
                 (45, 136),
                 (39, 132),
                 (30, 128),
                 (27, 124),
                 (25, 120),
                 (23, 116),
                 (20, 112),
                 (17, 108),
                 (15, 104),
                 (13, 100)
            ]
        elif qual == Qualification.II_Y:
            table = [
                 (250, 0),
                 (211, 205),
                 (185, 200),
                 (159, 195),
                 (120, 190),
                 (102, 185),
                 (90, 180),
                 (78, 175),
                 (60, 170),
                 (51, 165),
                 (45, 160),
                 (39, 155),
                 (30, 150),
                 (27, 145),
                 (25, 140),
                 (23, 135),
                 (20, 130),
                 (17, 125),
                 (15, 120),
                 (13, 115),
                 (11, 110),
                 (10, 105),
                 (7, 100)
            ]

        for i in range(len(table)):
            cur_value = table[i][0]
            if cur_value <= rank:
                return table[i][1]
        return 0

    def get_time_for_rank(self, leader_time, qual, rank):
        percent = self.get_percent_for_rank(qual, rank)
        assert isinstance(leader_time, OTime)
        msec_new = round(leader_time.to_msec() * percent / 100)
        ret = OTime(msec=msec_new)
        return ret


def get_start_list_data():
    pass


def get_result_data():
    """

    :return: {
        "title": str,
        "groups": [
            {
                "name": str,
                "persons": [
                    get_person_result_data
                    ...
                ]
            }
        ]
    }
    """
    data = []
    for group in race().groups:
        array = ResultCalculation().get_group_finishes(group)
        group_data = {
            'name': group.name,
            'persons': []
        }
        for res in array:
            assert isinstance(res, Result)
            person_data = get_person_result_data(res)
            group_data['persons'].append(person_data)
        data.append(group_data)
    ret = {'groups': data, 'title': 'Competition title'}

    return ret


def get_splits_data():
    pass


def get_splits_data_printout(person):
    ret = {}
    person_json = {}
    result_json = {}
    legs = []

    assert isinstance(person, Person)
    group = person.group
    course = group.course
    assert isinstance(course, Course)
    result = person.result

    person_json['name'] = person.full_name
    person_json['group'] = person.group.name
    person_json['bib'] = person.bib
    person_json['team'] = person.organization.name
    person_json['sportident_card'] = int(person.sportident_card)

    result_json['start'] = time_to_hhmmss(person.start_time)
    result_json['finish'] = time_to_hhmmss(result.finish_time)
    result_json['result'] = result.get_result()
    result_json['penalty_time'] = time_to_hhmmss(result.get_penalty_time())
    result_json['status'] = result.status
    result_json['place'] = result.place
    result_json['group_count_all'] = person.group.get_count_all()
    result_json['group_count_finished'] = person.group.get_count_finished()

    person_index = 0
    course_index = 0
    course_code = course.controls[course_index].code
    leg_start_time = result.get_start_time()
    start_time = result.get_start_time()

    while person_index < len(result.splits):
        cur_split = result.splits[person_index]
        cur_code = cur_split.code
        cur_time = cur_split.time

        leg = {}
        leg['code'] = cur_code
        leg['index'] = person_index
        leg['absolute_time'] = time_to_hhmmss(cur_time)
        leg['relative_time'] = time_to_hhmmss(cur_time - start_time)

        status = 'correct'
        if course_code == cur_code:
            leg_time = cur_time - leg_start_time
            leg_start_time = cur_time

            leg['leg_time'] = time_to_hhmmss(leg_time)
            leg['course_index'] = course_index

            leg['leg_speed'] = 'xx m/km'  # TODO calculate speed
            leg['leg_place'] = '1'  # TODO
            leg['leg_leader'] = 'John Smith'  # TODO
            leg['leg_best_time'] = '00:00:21'  # TODO

            course_index += 1
            if course_index >= len(course.controls):
                course_code = -1
            else:
                course_code = course.controls[course_index].code

        else:
            status = 'extra'

        leg['status'] = status
        legs.append(leg)

        person_index += 1

    ret['person'] = person_json
    ret['result'] = result_json
    ret['legs'] = legs

    return ret


def get_entry_statistics_data():
    pass


def get_team_statistics_data():
    pass


def get_person_result_data(res):
    person = res.person
    assert isinstance(person, Person)
    ret = {
        'name': person.full_name,
        'team': person.organization.name,
        'qual': person.qual.get_title(),
        'year': person.year,
        'penalty_time': time_to_hhmmss(res.get_penalty_time()),
        'result': res.get_result(),
        'place': res.place,
        'assigned_rank': res.assigned_rank.get_title()
    }
    return ret
