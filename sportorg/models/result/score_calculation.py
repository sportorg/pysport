import logging

from sportorg.models.memory import Result, Organization, RaceType
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.start.relay import get_team_result


class ScoreCalculation(object):

    def __init__(self, r):
        self.race = r

    def calculate_scores(self):
        logging.debug('Score calculation')
        for i in self.race.results:
            self.calculate_scores_result(i)

    def calculate_scores_result(self, result):
        if isinstance(result, Result):
            place = result.place
            if place > 0:
                place = int(place)
                scores_type = self.race.get_setting('scores_mode', 'off')
                if scores_type == 'array':
                    scores_array = str(self.race.get_setting('scores_array', '0')).split(',')
                    if len(scores_array):
                        if place > len(scores_array):
                            result.scores = int(scores_array[-1])
                        else:
                            result.scores = int(scores_array[place - 1])
                    else:
                        result.scores = 0
                elif scores_type == 'formula':
                    time_value = result.get_result_otime().to_msec()
                    leader_time_value = self.get_leader_time(result).to_msec()

                    time_phrase = 'time'
                    leader_time_phrase = 'leader'
                    expr = str(self.race.get_setting('scores_formula', '0'))
                    expr = expr.replace(time_phrase, str(time_value))
                    expr = expr.replace(leader_time_phrase, str(leader_time_value))
                    value = eval(expr)
                    value = max(round(value), 0)
                    result.scores = value
            else:
                result.scores = 0

    def get_leader_time(self, result):
        # find leader time in group
        if result and isinstance(result, Result):
            if result.person and result.person.group:
                group = result.person.group
                results = ResultCalculation(self.race).get_group_finishes(group)
                best_time = None
                for cur_result in results:
                    assert isinstance(cur_result, Result)
                    if self.race.get_type(group) == RaceType.RELAY:
                        cur_time = get_team_result(result.person)
                    else:
                        cur_time = cur_result.get_result_otime()
                    if not best_time or cur_time < best_time:
                        best_time = cur_time
                return best_time
        return None

    def get_group_team_results(self, group, team):
        ret = []
        for result in self.race.results:
            if result.person and result.person.group == group:
                if result.person.organization == team:
                    ret.append(result)
        return ret

    def get_group_region_results(self, group, region):
        ret = []
        for result in self.race.results:
            if result.person and result.person.group == group:
                if self.get_region_for_organization(result.person.organization) == region:
                    ret.append(result)
        return ret

    @staticmethod
    def get_region_for_organization(org):
        if org:
            assert isinstance(org, Organization)
            if org.address:
                if org.address.state:
                    return org.address.state
        return None

    def get_all_regions(self):
        ret = []
        for i in self.race.organizations:
            region = self.get_region_for_organization(i)
            if region and region not in ret:
                ret.append(region)
        return ret
