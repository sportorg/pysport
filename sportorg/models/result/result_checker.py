import logging

from sportorg.common.otime import OTime
from sportorg.models.memory import (
    Person,
    Result,
    ResultSportident,
    ResultStatus,
    find,
    race,
)


class ResultCheckerException(Exception):
    pass


class ResultChecker:
    def __init__(self, person: Person):
        self.person = person

    def check_result(self, result: ResultSportident):
        if self.person is None:
            return True
        if self.person.group is None:
            return True

        if race().get_setting('result_processing_mode', 'time') == 'scores':
            # process by score (rogain)
            result.scores_rogain = self.calculate_scores_rogain(result)
            return True

        course = race().find_course(result)

        if race().get_setting('marked_route_dont_dsq', False):
            # mode: competition without disqualification for mispunching (add penalty for missing cp)
            result.check(course)
            return True

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
        if result.status in [
            ResultStatus.OK,
            ResultStatus.MISSING_PUNCH,
            ResultStatus.OVERTIME,
            ResultStatus.MISS_PENALTY_LAP,
        ]:
            result.status = ResultStatus.OK
            if not o.check_result(result):
                result.status = ResultStatus.MISSING_PUNCH
                result.status_comment = 'п.п.3.13.12.2'

            elif not cls.check_penalty_laps(result):
                result.status = ResultStatus.MISS_PENALTY_LAP
            elif result.person.group and result.person.group.max_time.to_msec():
                if result.get_result_otime() > result.person.group.max_time:
                    if race().get_setting('result_processing_mode', 'time') == 'time':
                        result.status = ResultStatus.OVERTIME
                        result.status_comment = 'п.п.5.4.7'

        return o

    @staticmethod
    def check_all():
        logging.debug('Checking all results')
        for result in race().results:
            if result.person:
                ResultChecker.checking(result)
                ResultChecker.calculate_penalty(result)

    @staticmethod
    def calculate_penalty(result: Result):
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
        splits = result.splits

        if mode == 'laps' and race().get_setting('marked_route_if_station_check'):
            lap_station = race().get_setting('marked_route_penalty_lap_station_code')
            splits, _ = ResultChecker.detach_penalty_laps2(splits, lap_station)

        if race().get_setting('marked_route_dont_dsq', False):
            # free order, don't penalty for extra cp
            penalty = ResultChecker.penalty_calculation_free_order(splits, controls)
        else:
            # marked route with penalty
            penalty = ResultChecker.penalty_calculation(
                splits, controls, check_existence=True
            )

        if race().get_setting('marked_route_max_penalty_by_cp', False):
            # limit the penalty by quantity of controls
            penalty = min(len(controls), penalty)

        if mode == 'laps':
            result.penalty_laps = penalty
            if result.status == ResultStatus.OK:
                ResultChecker.marked_route_check_penalty_laps(result)

        elif mode == 'time':
            time_for_one_penalty = OTime(
                msec=race().get_setting('marked_route_penalty_time', 60000)
            )
            result.penalty_time = time_for_one_penalty * penalty

    @staticmethod
    def get_marked_route_incorrect_list(controls):
        ret = []
        for i in controls:
            code_str = str(i.code)
            if code_str and '(' in code_str:
                correct = code_str.split('(')[0].strip()
                if correct.isdigit():
                    for cp in code_str.split('(')[1].split(','):
                        cp = cp.strip(')').strip()
                        if cp != correct and cp.isdigit():
                            ret.append(cp)
        return ret

    @staticmethod
    def penalty_calculation(splits, controls, check_existence=False):
        """:return quantity of incorrect or duplicated punches, order is ignored
        ```
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

        wildcard support for free order
        origin: *,*,* athlete: 31; result:2          // wrong:
                                                     // returns 0 if check_existence=False
                                                     // returns 2 if check_existence=True
        origin: *,*,* athlete: 31,31; result:2       // wrong:
                                                     // returns 0 if check_existence=False
                                                     // returns 1 if check_existence=True
        origin: *,*,* athlete: 31,31,31,31; result:3 // wrong:
                                                     // returns 1 if check_existence=False
                                                     // returns 1 if check_existence=True
        ```
        """

        user_array = [i.code for i in splits]
        origin_array = [i.get_number_code() for i in controls]
        res = 0

        # может дать 0 штрафа при мусоре в чипе
        if check_existence and len(user_array) < len(origin_array):
            # add 1 penalty score for missing points
            res = len(origin_array) - len(user_array)

        incorrect_array = ResultChecker.get_marked_route_incorrect_list(controls)

        if len(incorrect_array) > 0:
            # marked route with choice, controls like 31(31,131), penalty only wrong choice (once),
            # ignoring controls from another courses, previous punches on uncleared card, duplicates
            # this mode allows combination of marked route and classic course, but please use different controls
            for i in incorrect_array:
                if i in user_array:
                    res += 1
        else:
            # classic penalty model - count correct control punch only once, others are recognized as incorrect
            # used for orientathlon, corridor training with choice
            for i in origin_array:
                # remove correct points (only one object per loop)
                if i == '0' and len(user_array):
                    del user_array[0]

                elif i in user_array:
                    user_array.remove(i)

            # now user_array contains only incorrect and duplicated values
            res += len(user_array)

        return res

    @staticmethod
    def penalty_calculation_free_order(splits, controls):
        """:return quantity penalty, duplication checked
        ```
        origin: * ,* ,* ; athlete: 31,41,51; result:0
        origin: * ,* ,* ; athlete: 31,31,51; result:1
        origin: * ,* ,* ; athlete: 31,31,31; result:2
        origin: * ,* ,* ; athlete: 31; result:2

        support of first/last mandatory cp
        origin: 40,* ,* ,90; athlete: 40,31,32,90; result:0
        origin: 40,* ,* ,90; athlete: 40,31,40,90; result:1
        origin: 40,* ,* ,90; athlete: 40,40,40,90; result:2
        origin: 40,* ,* ,90; athlete: 40,90,90,90; result:2
        origin: 40,* ,* ,90; athlete: 31,32,33,90; result:4
        origin: 40,* ,* ,90; athlete: 31,40,31,90; result:1
        origin: 40,* ,* ,90; athlete: 31,40,90,41; result:1
        origin: 40,* ,* ,90; athlete: 31,40,31,32; result:1
        origin: 40,* ,* ,90; athlete: 31,40,31,40; result:2
        origin: 40,* ,* ,90; athlete: 40,40,90,90; result:2
        origin: 40,* ,* ,90; athlete: 40,41,90,90; result:0 TODO:1 - only one incorrect case
        ```
        """
        res = 0
        correct_count = 0
        for i in splits:
            if not i.has_penalty:
                correct_count += 1

        res += max(len(controls) - correct_count, 0)

        return res

    @staticmethod
    def detach_penalty_laps(splits, lap_station):
        if not splits:
            return [], []
        for idx, punch in enumerate(reversed(splits)):
            if int(punch.code) != lap_station:
                break
        else:
            idx = len(splits)
        idx = len(splits) - idx
        return splits[:idx], splits[idx:]

    @staticmethod
    def detach_penalty_laps2(splits, lap_station):
        '''Detaches penalty laps from the given list of splits
        based on the provided lap station code.
        '''
        if not splits:
            return [], []
        regular = [punch for punch in splits if int(punch.code) != lap_station]
        penalty = [punch for punch in splits if int(punch.code) == lap_station]
        return regular, penalty

    @staticmethod
    def check_penalty_laps(result):
        assert isinstance(result, Result)

        mode = race().get_setting('marked_route_mode', 'off')
        check_laps = race().get_setting('marked_route_if_station_check')

        if mode == 'laps' and check_laps:
            lap_station = race().get_setting('marked_route_penalty_lap_station_code')
            _, penalty_laps = ResultChecker.detach_penalty_laps2(
                result.splits, lap_station
            )
            num_penalty_laps = len(penalty_laps)

            if num_penalty_laps < result.penalty_laps:
                return False

        return True

    @staticmethod
    def get_control_score(code):
        obj = race()
        control = find(obj.controls, code=str(code))
        if control and control.score:
            return control.score

        if obj.get_setting('result_processing_score_mode', 'fixed') == 'fixed':
            return obj.get_setting(
                'result_processing_fixed_score_value', 1.0
            )  # fixed score per control
        else:
            return int(code) // 10  # score = code / 10

    @staticmethod
    def calculate_scores_rogain(result):
        user_array = []
        ret = 0

        allow_duplicates = race().get_setting(
            'result_processing_scores_allow_duplicates', False
        )

        for cur_split in result.splits:
            code = str(cur_split.code)
            if code not in user_array or allow_duplicates:
                user_array.append(code)
                ret += ResultChecker.get_control_score(code)
        if result.person and result.person.group:
            user_time = result.get_result_otime()
            max_time = result.person.group.max_time
            if OTime() < max_time < user_time:
                time_diff = user_time - max_time
                seconds_diff = time_diff.to_sec()
                minutes_diff = (seconds_diff + 59) // 60  # note, 1:01 = 2 minutes
                penalty_step = race().get_setting(
                    'result_processing_scores_minute_penalty', 1.0
                )
                ret -= minutes_diff * penalty_step
        if ret < 0:
            ret = 0
        return ret

    @staticmethod
    def marked_route_check_penalty_laps(result: Result):
        obj = race()

        mr_if_counting_lap = obj.get_setting('marked_route_if_counting_lap', False)
        mr_if_station_check = obj.get_setting('marked_route_if_station_check', False)
        mr_station_code = obj.get_setting('marked_route_penalty_lap_station_code', 0)

        if mr_if_station_check and int(mr_station_code) > 0:
            count_laps = 0
            if mr_if_counting_lap:
                count_laps = -1

            for split in result.splits:
                if str(split.code) == str(mr_station_code):
                    count_laps += 1

            if count_laps < result.penalty_laps:
                result.status = ResultStatus.MISSING_PUNCH
                result.status_comment = 'п.п.4.6.12.7'
