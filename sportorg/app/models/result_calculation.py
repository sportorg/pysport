from sportorg.app.models.memory import race, Result, Person, ResultStatus, Course, Group
from sportorg.app.plugins.utils.utils import time_to_hhmmss
from sportorg.language import _


class ResultCalculation(object):
    def process_results(self):
        self.set_times()
        for i in race().groups:
            array = self.get_group_finishes(i)
            self.set_places(array)

    def set_times(self):
        for i in race().results:
            assert isinstance(i, Result)
            person = i.person
            if person:
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
            if res.status == ResultStatus.OK or res.status == 0:
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


def get_start_list_data():
    pass


def get_result_data():
    ret = {}
    data = {}
    for group in race().groups:
        array = ResultCalculation().get_group_finishes(group)
        group_data = []
        for res in array:
            assert isinstance(res, Result)
            person_data = get_person_result_data(res)
            group_data.append(person_data)
        data[group.name] = group_data
    ret['data'] = data
    ret['title'] = 'Competition title'
    ret['table_titles'] = ['name', 'team', 'qual', 'year', 'result', 'place']

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

    person_json['name'] = person.surname + ' ' + person.name
    person_json['group'] = person.group.name
    person_json['bib'] = person.bib
    person_json['team'] = person.organization.name
    person_json['card_number'] = person.card_number

    result_json['start'] = time_to_hhmmss(person.start_time)
    result_json['finish'] = time_to_hhmmss(result.finish_time)
    result_json['result'] = result.get_result()
    result_json['status'] = result.status
    result_json['place'] = result.place
    result_json['group_count_all'] = person.group.get_count_all()
    result_json['group_count_finished'] = person.group.get_count_finished()

    person_index = 0
    course_index = 0
    course_code = course.controls[course_index].code
    leg_start_time = result.get_start_time()
    start_time = result.get_start_time()

    while person_index < len(result.punches):
        cur_punch = result.punches[person_index]
        cur_code = cur_punch[0]
        cur_time = cur_punch[1]

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
    ret = []
    person = res.person
    assert isinstance(person, Person)
    ret.append(person.surname + ' ' + person.name)
    ret.append(person.organization.name)
    ret.append(person.qual)
    ret.append(person.year)
    ret.append(res.get_result())
    ret.append(res.place)
    return ret