import logging

from sportorg.core.otime import OTime
from sportorg.models.constant import StatusComments
from sportorg.models.memory import Person, ResultStatus, race, Result, find


class ResultCheckerException(Exception):
    pass


class ResultChecker:
    def __init__(self, person: Person):
        assert person, Person
        self.person = person

    def check_result(self, result):
        if self.person is None:
            return True
        if self.person.group is None:
            return True

        if race().get_setting('result_processing_mode', 'time') == 'scores':
            # process by score (rogain)
            result.scores = self.calculate_scores_rogain(result)
            return True

        course = race().find_course(result)

        if course is None:
            if self.person.group.is_any_course:
                return False
            return True

        if self.person.group.is_any_course:
            return True

        return result.check(course)

    @classmethod
    def checking(cls, result):
        if result.person is None:
            raise ResultCheckerException('Not person')
        o = cls(result.person)
        if result.status in [ResultStatus.OK, ResultStatus.DISQUALIFIED, ResultStatus.OVERTIME]:
            result.status = ResultStatus.OK
            if not o.check_result(result):
                result.status = ResultStatus.DISQUALIFIED
                if not result.status_comment:
                    result.status_comment = StatusComments().remove_hint(StatusComments().get())
            elif result.person.group and result.person.group.max_time.to_msec():
                if result.get_result_otime() > result.person.group.max_time:
                    if race().get_setting('result_processing_mode', 'time') == 'time':
                        result.status = ResultStatus.OVERTIME

        return o

    @classmethod
    def check_all(cls):
        logging.debug('Checking all results')
        for result in race().results:
            if result.person is not None:
                ResultChecker.checking(result)

    @staticmethod
    def calculate_penalty(result):
        assert isinstance(result, Result)
        mode = race().get_setting('marked_route_mode', 'off')
        if mode == 'off':
            return

        person = result.person

        if person is None:
            return
        if person.group is None:
            return

        course = race().find_course(result)
        if not course:
            return

        controls = course.controls

        penalty = ResultChecker.penalty_calculation(result.splits, controls, check_existence=True)

        if mode == 'laps':
            result.penalty_laps = penalty
        elif mode == 'time':
            time_for_one_penalty = OTime(msec=race().get_setting('marked_route_penalty_time', 60000))
            result.penalty_time = time_for_one_penalty * penalty

    @staticmethod
    def penalty_calculation(splits, controls, check_existence=False):
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
        user_array = [i.code for i in splits]
        origin_array = [i.get_number_code() for i in controls]
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

    @staticmethod
    def get_control_score(code):
        obj = race()
        control = find(obj.controls, code=str(code))
        if control and control.score:
            return control.score

        if obj.get_setting('result_processing_score_mode', 'fixed') == 'fixed':
            return obj.get_setting('result_processing_fixed_score_value', 1.0)  # fixed score per control
        else:
            return int(code) // 10  # score = code / 10

    @staticmethod
    def calculate_scores_rogain(result):
        user_array = []
        ret = 0
        for cur_split in result.splits:
            code = str(cur_split.code)
            if code not in user_array:
                user_array.append(code)
                ret += ResultChecker.get_control_score(code)
        if result.person and result.person.group:
            user_time = result.get_result_otime()
            max_time = result.person.group.max_time
            if OTime() < max_time < user_time:
                time_diff = user_time - max_time
                seconds_diff = time_diff.to_sec()
                minutes_diff = (seconds_diff + 59) // 60  # note, 1:01 = 2 minutes
                penalty_step = race().get_setting('result_processing_scores_minute_penalty', 1.0)
                ret -= minutes_diff * penalty_step
        if ret < 0:
            ret = 0
        return ret


