import logging

from sportorg.common.otime import OTime
from sportorg.models.memory import RaceType, Result
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.start.relay import get_team_result


class ScoreCalculation(object):
    def __init__(self, r):
        self.race = r
        self.formula = None
        self.wrong_formula = False
        if self.race.get_setting('scores_mode', 'off') == 'formula':
            self.formula = str(self.race.get_setting('scores_formula', '0'))

    def get_scores_by_formula(self, leader, time):
        if self.formula and not self.wrong_formula:
            try:
                return max(eval(self.formula, {}, {'leader': leader, 'time': time}), 0)
            except Exception as e:
                logging.error(str(e))
                self.wrong_formula = True
        return 0

    def calculate_scores(self):
        logging.debug('Score calculation')
        for i in self.race.results:
            self.calculate_scores_result(i)

    def calculate_scores_result(self, result):
        if isinstance(result, Result) and result.person and result.person.group:
            place = int(result.place)
            if self.race.get_type(
                result.person.group
            ) == RaceType.RELAY and get_team_result(result.person) == OTime(0):
                place = 0
            if place > 0:
                scores_type = self.race.get_setting('scores_mode', 'off')
                if scores_type == 'array':
                    scores_array = str(
                        self.race.get_setting('scores_array', '0')
                    ).split(',')
                    if len(scores_array):
                        if place > len(scores_array):
                            result.scores = int(scores_array[-1])
                        else:
                            result.scores = int(scores_array[place - 1])
                    else:
                        result.scores = 0
                elif scores_type == 'formula':
                    if self.race.get_type(result.person.group) == RaceType.RELAY:
                        time_value = get_team_result(result.person).to_msec()
                    else:
                        time_value = result.get_result_otime().to_msec()
                    leader_time = self.get_leader_time(result)
                    if leader_time:
                        leader_time_value = leader_time.to_msec()
                    else:
                        leader_time_value = 1000
                    result.scores = self.get_scores_by_formula(
                        leader_time_value, time_value
                    )
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
                    if not cur_result.is_status_ok():
                        continue
                    if self.race.get_type(group) == RaceType.RELAY:
                        cur_time = get_team_result(cur_result.person)
                    else:
                        cur_time = cur_result.get_result_otime()
                    if not best_time or cur_time < best_time:
                        if cur_time > OTime(0):
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
                if (
                    self.get_region_for_organization(result.person.organization)
                    == region
                ):
                    ret.append(result)
        return ret

    @staticmethod
    def get_region_for_organization(org):
        if org:
            if org.region:
                return org.region
        return None

    def get_all_regions(self):
        ret = []
        for i in self.race.organizations:
            region = self.get_region_for_organization(i)
            if region and region not in ret:
                ret.append(region)
        return ret
