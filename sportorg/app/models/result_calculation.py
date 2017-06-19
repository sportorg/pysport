from sportorg.app.models.memory import race, Result, Person, ResultStatus


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
        return ret

    def set_places(self, array):
         assert isinstance(array, list)
         array.sort()
         for i in range(len(array)):
            res = array[i]
            assert isinstance(res, Result)

            if res.status == ResultStatus.OK or res.status == 0:
                # give place only if status = OK
                res.place = i+1

                # the same place
                if i > 0 and res.result == array[i-1].result:
                    res.place = array[i-1].place
