from ast import literal_eval

from sportorg.models.memory import Result, race
from sportorg.models.result.result_calculation import ResultCalculation


class ScoreCalculation(object):
    @staticmethod
    def calculate_scores():
        obj = race()
        for i in obj.results:
            ScoreCalculation.calculate_scores_result(i)

    @staticmethod
    def calculate_scores_result(result):
        obj = race()
        if isinstance(result, Result):
            place = result.place
            if place:
                scores_type = obj.get_setting('scores_type', 'off')
                if scores_type == 'array':
                    scores_array = str(obj.get_setting('scores_array', '0')).split(',')
                    if len(scores_array):
                        if place > len(scores_array):
                            result.scores = scores_array[-1]
                        else:
                            result.scores = scores_array[place - 1]
                    else:
                        result.scores = 0
                elif scores_type == 'formula':
                    time_value = result.get_result_otime().to_msec()
                    leader_time_value = ScoreCalculation.get_leader_time(result).to_msec()

                    time_phrase = 'time'
                    leader_time_phrase = 'leader'
                    expr = str(obj.get_setting('scores_formula', '0'))
                    expr = expr.replace(time_phrase, time_value)
                    expr = expr.replace(leader_time_phrase, leader_time_value)

                    value = round(float(literal_eval(expr)))
                    result.scores = value

    @staticmethod
    def get_leader_time(result):
        # find leader time in group
        if result and isinstance(result, Result):
            if result.person and result.person.group:
                group = result.person.group
                results = ResultCalculation.get_group_finishes(group)
                best_time = None
                for cur_result in results:
                    assert isinstance(cur_result, Result)
                    cur_time = cur_result.get_result_otime()
                    if not best_time or cur_time < best_time:
                        best_time = cur_time
                return best_time
        return None


