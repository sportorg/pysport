from sportorg.models.memory import Person, ResultStatus, SystemType


class ResultCheckerException(Exception):
    pass


class ResultChecker:
    def __init__(self, person: Person):
        assert person, Person
        self.person = person

    @staticmethod
    def check(splits, controls):
        """

        :param splits: [Split, ...]
        :param controls: [CourseControl, ...]
        :return:
        """
        i = 0
        count_controls = len(controls)
        if count_controls == 0:
            return True

        for split in splits:
            try:
                template = str(controls[i].code)
                cur_code = int(split.code)

                list_exists = False
                list_contains = False
                ind_begin = template.find('(')
                ind_end = template.find(')')
                if ind_begin > 0 and ind_end > 0:
                    list_exists = True
                    # any control from the list e.g. '%(31,32,33)'
                    arr = template[ind_begin + 1:ind_end].split(',')
                    if str(cur_code) in arr:
                        list_contains = True

                if template.startswith('%'):
                    # non-unique control
                    if not list_exists or list_contains:
                        # any control '%' or '%(31,32,33)'
                        i += 1

                elif template.startswith('*'):
                    # unique control '*' or '*(31,32,33)'
                    if list_exists and not list_contains:
                        # not in list
                        continue
                    # test previous splits
                    is_unique = True
                    for prev_split in splits[0:i]:
                        if int(prev_split.code) == cur_code:
                            is_unique = False
                            break
                    if is_unique:
                        i += 1

                else:
                    # simple pre-ordered control '31 989' or '31(31,32,33) 989'
                    if list_exists:
                        # control with optional codes '31(31,32,33) 989'
                        if list_contains:
                            i += 1
                    else:
                        # just cp '31 989'
                        is_equal = cur_code == int(controls[i].code)
                        if is_equal:
                            i += 1

                if i == count_controls:
                    return True

            except KeyError:
                return False

        return False

    def check_result(self, result):
        if self.person is None:
            return True
        if self.person.group is None:
            return True

        controls = self.person.group.course.controls

        if not hasattr(controls, '__iter__'):
            return True

        if result.system_type != SystemType.SPORTIDENT:
            return True

        return self.check(result.splits, controls)

    @classmethod
    def checking(cls, result):
        if result.person is None:
            raise ResultCheckerException('Not person')
        o = cls(result.person)
        result.status = ResultStatus.OK
        if not o.check_result(result):
            result.status = ResultStatus.DISQUALIFIED
        if not result.finish_time:
            result.status = ResultStatus.DID_NOT_FINISH

        return o
