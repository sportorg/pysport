from fnmatch import translate

from sportorg.app.models.memory import race, Result, Person, ResultStatus
from sportorg.language import locale


class ResultCalculation(object):
    def process_results(self):
        for i in race().groups:
            array = self.get_group_finishes(i)
            self.set_places(array)

    def get_group_finishes(self, group):
        ret = list()
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
                    res.place = ('o/c')  # TODO:translate
                    continue

                # the same place processing
                if current_place == 1 or res.result != last_result:
                    # result differs from previous - give next place
                    last_result = res.result
                    last_place = current_place

                res.place = last_place
                current_place += 1
