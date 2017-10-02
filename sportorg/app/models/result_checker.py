from .memory import Person, Result


class ResultChecker:
    def __init__(self, person: Person):
        assert person, Person
        self.person = person

    @staticmethod
    def check(punches, controls):
        """
        
        :param punches: [(code, datetime()), ...]
        :param controls: [model.CourseControl, ...]
        :return: 
        """
        i = 1
        for punch in punches:
            try:
                is_equal = int(punch[0]) == int(controls[i].code)
                if is_equal:
                    i += 1
            except KeyError:
                return False
        count_controls = len(controls)
        if i == count_controls:
            return True

        return False

    def check_result(self, result: Result):
        if self.person.group is None:
            return True

        controls = self.person.group.course.controls

        if not hasattr(controls, '__iter__'):
            return True

        return self.check(result.punches, controls)
