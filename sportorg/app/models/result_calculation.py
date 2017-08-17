from sportorg.app.models.memory import race, Result, Person, ResultStatus
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
            i.start_time = person.start_time
            i.result = i.get_result_for_sort()

    def get_group_finishes(self, group):
        ret = []
        for i in race().results:
            assert isinstance(i, Result)
            person = i.person
            assert isinstance(person, Person)
            if person.group == group:
                ret.append(i)
        ret.sort()
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