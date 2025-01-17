import logging

from sportorg.common.otime import OTime
from sportorg.models.constant import StatusComments
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

        if race().get_setting("result_processing_mode", "time") == "ardf":
            result.scores_ardf = self.calculate_scores_ardf(result)
            return True
        elif race().get_setting("result_processing_mode", "time") == "scores":
            # process by score (rogaine)
            allow_duplicates = race().get_setting(
                "result_processing_scores_allow_duplicates", False
            )
            penalty_step = race().get_setting(
                "result_processing_scores_minute_penalty", 1
            )

            score = self.calculate_rogaine_score(result, allow_duplicates)
            penalty = self.calculate_rogaine_penalty(result, score, penalty_step)
            result.rogaine_score = score - penalty
            result.rogaine_penalty = penalty
            return True

        course = race().find_course(result)

        if race().get_setting("marked_route_dont_dsq", False):
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
            raise ResultCheckerException("Not person")
        o = cls(result.person)
        if result.status in [
            ResultStatus.OK,
            ResultStatus.MISSING_PUNCH,
            ResultStatus.OVERTIME,
            ResultStatus.MISS_PENALTY_LAP,
        ]:
            result.status = ResultStatus.OK

            check_flag = o.check_result(result)
            ResultChecker.calculate_penalty(result)
            ResultChecker.calculate_credit_time(result)
            if not check_flag:
                result.status = ResultStatus.MISSING_PUNCH

            elif not cls.check_penalty_laps(result):
                result.status = ResultStatus.MISS_PENALTY_LAP

            elif result.person.group and result.person.group.max_time.to_msec():
                rp_mode = race().get_setting("result_processing_mode", "time")
                result_time = result.get_result_otime()
                max_time = result.person.group.max_time
                if rp_mode in ("time", "ardf"):
                    if result_time > max_time:
                        result.status = ResultStatus.OVERTIME
                elif rp_mode == "scores":
                    max_overrun_time = OTime(
                        msec=race().get_setting(
                            "result_processing_scores_max_overrun_time", 0
                        )
                    )
                    if (
                        max_overrun_time.to_msec() > 0
                        and result_time > max_time + max_overrun_time
                    ):
                        result.status = ResultStatus.OVERTIME

            result.status_comment = StatusComments().get_status_default_comment(
                result.status
            )

        return o

    @staticmethod
    def check_all():
        logging.debug("Checking all results")
        for result in race().results:
            if result.person:
                ResultChecker.checking(result)

    @staticmethod
    def calculate_credit_time(result: Result):
        credit_time_enabled = race().get_setting("credit_time_enabled", False)
        if not credit_time_enabled:
            return

        credit_cp = race().get_setting("credit_time_cp", 250)
        splits = result.splits

        result.credit_time = ResultChecker.credit_calculation(splits, credit_cp)

    @staticmethod
    def calculate_penalty(result: Result):
        mode = race().get_setting("marked_route_mode", "off")
        if mode == "off":
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

        # use prefixes _min and _lap in group name to force non-standard penalty
        # TODO move setting to group properties
        if person.group.name.lower().find("_min") > -1:
            mode = "time"
        if person.group.name.lower().find("_lap") > -1:
            mode = "laps"

        if mode == "laps" and race().get_setting("marked_route_if_station_check"):
            lap_station = race().get_setting("marked_route_penalty_lap_station_code")
            splits, _ = ResultChecker.detach_penalty_laps2(splits, lap_station)

        if race().get_setting("marked_route_dont_dsq", False):
            # free order, don't penalty for extra cp
            penalty = ResultChecker.penalty_calculation_free_order(splits, controls)
        else:
            # marked route with penalty
            penalty = ResultChecker.penalty_calculation(
                splits, controls, check_existence=True
            )

        if race().get_setting("marked_route_max_penalty_by_cp", False):
            # limit the penalty by quantity of controls
            penalty = min(len(controls), penalty)

        result.penalty_laps = 0
        result.penalty_time = OTime()

        if mode == "laps":
            result.penalty_laps = penalty
        elif mode == "time":
            time_for_one_penalty = OTime(
                msec=race().get_setting("marked_route_penalty_time", 60000)
            )
            result.penalty_time = time_for_one_penalty * penalty

    @staticmethod
    def get_marked_route_incorrect_list(controls):
        ret = []
        for i in controls:
            code_str = str(i.code)
            if code_str and "(" in code_str:
                correct = code_str.split("(")[0].strip()
                if correct.isdigit():
                    for cp in code_str.split("(")[1].split(","):
                        cp = cp.strip(")").strip()
                        if cp != correct and cp.isdigit():
                            if cp not in ret:
                                ret.append(cp)
        return ret

    @staticmethod
    def credit_calculation(splits, credit_cp):
        result_credit_time = OTime()
        for idx, split in enumerate(splits):
            if int(split.code) == credit_cp and idx > 0:
                result_credit_time += split.time - splits[idx - 1].time

        return result_credit_time

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

        # In theory can return less penalty for uncleaned card / может дать 0 штрафа при мусоре в чипе
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
                if i == "0" and len(user_array):
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
        """Detaches penalty laps from the given list of splits
        based on the provided lap station code.
        """
        if not splits:
            return [], []
        regular = [
            punch
            for punch in splits
            if (punch.is_correct or int(punch.code) != lap_station)
        ]
        penalty = [
            punch
            for punch in splits
            if (int(punch.code) == lap_station and not punch.is_correct)
        ]
        return regular, penalty

    @staticmethod
    def check_penalty_laps(result):
        assert isinstance(result, Result)

        mode = race().get_setting("marked_route_mode", "off")
        check_laps = race().get_setting("marked_route_if_station_check")

        if mode == "laps" and check_laps:
            lap_station = race().get_setting("marked_route_penalty_lap_station_code")
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

        if obj.get_setting("result_processing_score_mode", "fixed") == "fixed":
            return obj.get_setting(
                "result_processing_fixed_score_value", 1.0
            )  # fixed score per control
        else:
            return int(code) // 10  # score = code / 10

    @staticmethod
    def calculate_rogaine_score(result: Result, allow_duplicates: bool = False) -> int:
        """
        Calculates the rogaine score for a given result.

        Parameters:
            result (Result): The result for which the rogaine score needs to be calculated.
            allow_duplicates (bool, optional): Whether to allow duplicate control points. Defaults to False.

        Returns:
            int: The calculated rogaine score.

        If `allow_duplicates` flag is `True`, the function allows duplicate control points
        to be included in the score calculation.
        """
        user_array = []
        score = 0

        for cur_split in result.splits:
            code = str(cur_split.code)
            if code not in user_array or allow_duplicates:
                user_array.append(code)
                score += ResultChecker.get_control_score(code)

        return score

    @staticmethod
    def calculate_rogaine_penalty(
        result: Result, score: int, penalty_step: int = 1
    ) -> int:
        """
        Calculates the penalty for a given result based on the participant's excess of a race time.

        Parameters:
            result (Result): The result for which the penalty needs to be calculated.
            score (int): The competitor's score.
            penalty_step (int, optional): The penalty points for each minute late. Defaults to 1.

        Returns:
            int: The calculated penalty for the result.

        """
        penalty = 0
        if result.person and result.person.group:
            user_time = result.get_result_otime()
            max_time = result.person.group.max_time
            if OTime() < max_time < user_time:
                time_diff = user_time - max_time
                seconds_diff = time_diff.to_sec()
                minutes_diff = (seconds_diff + 59) // 60  # note, 1:01 = 2 minutes
                penalty = minutes_diff * penalty_step

        # result = score - penalty >= 0
        penalty = min(penalty, score)

        return penalty

    @staticmethod
    def calculate_scores_ardf(result):
        user_array = []
        ret = 0

        course = race().find_course(result)
        if not course:
            return ret

        correct_order = [str(control.code) for control in course.controls]

        index_in_order = 0

        for cur_split in result.splits:
            code = str(cur_split.code)

            initial_index = index_in_order

            while index_in_order < len(correct_order):
                current_cp = correct_order[index_in_order]

                if "?" in current_cp:
                    if "(" in current_cp and ")" in current_cp:
                        options = current_cp.strip("?()").split(",")
                        if code in options and code not in user_array:
                            user_array.append(code)
                            ret += 1
                            index_in_order = initial_index + 1
                            break
                    else:
                        if code not in user_array:
                            user_array.append(code)
                            ret += 1
                            index_in_order = initial_index + 1
                            break

                    index_in_order += 1
                    continue

                if code == current_cp:
                    if code not in user_array:
                        user_array.append(code)
                        ret += 1
                    index_in_order += 1
                    break

                index_in_order = initial_index
                break

        if result.person and result.person.group:
            user_time = result.get_result_otime()
            max_time = result.person.group.max_time
            if OTime() < max_time < user_time:
                result.status = ResultStatus.DISQUALIFIED
                return 0

        return ret
