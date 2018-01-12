from gettext import find

from sportorg.core.otime import OTime
from sportorg.models.memory import Person, ResultStatus, SystemType, find, race, Result, CourseControl


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

        if result.system_type != SystemType.SPORTIDENT:
            return True

        course = find_course(self.person)
        if not course:
            return True

        controls = course.controls

        if not hasattr(controls, '__iter__'):
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

    @staticmethod
    def calculate_penalty(result):
        assert isinstance(result, Result)
        mode = race().get_setting('marked_route_mode', 'off')
        if mode == 'off':
            return

        person = result.person

        if person is None:
            return True
        if person.group is None:
            return True

        if result.system_type != SystemType.SPORTIDENT:
            return True

        course = find_course(person)
        if not course:
            return True

        controls = course.controls

        if not hasattr(controls, '__iter__'):
            return True

        penalty = ResultChecker.penalty_calculation(result.splits, controls)

        if mode == 'laps':
            result.penalty_laps = penalty
        elif mode == 'time':
            time_for_one_penalty = race().get_setting('marked_route_penalty_time', OTime(sec=60))
            result.penalty_time = time_for_one_penalty * penalty

    @staticmethod
    def penalty_calculation(splits, controls, check_existence=False):
        user_array = [i.code for i in splits]
        origin_array = [i.get_int_code() for i in controls]
        return ResultChecker.penalty_calculation_int(user_array, origin_array, check_existence)

    @staticmethod
    def penalty_calculation_int(user_array, origin_array, check_existence=False):
        """:return quantity of incorrect or duplicated punches, order is ignored
            origin: 31,41,51; athlete: 31,41,51; result:0
            origin: 31,41,51; athlete: 31; result:0
            origin: 31,41,51; athlete: 41,31,51; result:0
            origin: 31,41,51; athlete: 31,42,51; result:1
            origin: 31,41,51; athlete: 31,41,51,52; result:1
            origin: 31,41,51; athlete: 31,42,51,52; result:2
            origin: 31,41,51; athlete: 31,31,41,51; result:1
            origin: 31,41,51; athlete: 31,41,51,51; result:1
            origin: 31,41,51; athlete: 32,42,52; result:3
            origin: 31,41,51; athlete: 31,41,51,61,71,81,91; result:4
            origin: 31,41,51; athlete: 31,41,52,61,71,81,91; result:5
            origin: 31,41,51; athlete: 51,61,71,81,91,31,41; result:4
            origin: 31,41,51; athlete: 51,61,71,81,91,32,41; result:5
            origin: 31,41,51; athlete: 51,61,71,81,91,32,42; result:6
            origin: 31,41,51; athlete: 52,61,71,81,91,32,42; result:7
            origin: 31,41,51; athlete: no punches; result:0

            with existence checking (if athlete has less punches, each missing add penalty):
            origin: 31,41,51; athlete: 31; result:2
            origin: 31,41,51; athlete: no punches; result:3
        """
        res = 0
        if check_existence and len(user_array) < len(origin_array):
            # add 1 penalty score for missing points
            res = len(origin_array) - len(user_array)

        for i in origin_array:
            # remove correct points (only one object per loop)
            if i in user_array:
                user_array.remove(i)

        # now user_array contains only incorrect and duplicated values
        res += len(user_array)

        return res


def find_course(person):
    # first get course by number
    bib = person.bib
    obj = race()
    ret = find(obj.courses, name=str(bib))
    if not ret and bib > 1000:
        course_name = "{}.{}".format(bib % 1000, bib // 1000)
        ret = find(obj.courses, name=course_name)
    # usual connection via group
    if not ret:
        if person.group:
            ret = person.group.course
    return ret

