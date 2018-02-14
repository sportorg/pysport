from sportorg.models.memory import Result, race, Organization, RaceType
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.start.relay import get_leg_count, get_team_result


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
            if place and (isinstance(place, int) or place.isdigit()):
                place = int(place)
                scores_type = obj.get_setting('scores_mode', 'off')
                if scores_type == 'array':
                    scores_array = str(obj.get_setting('scores_array', '0')).split(',')
                    if len(scores_array):
                        if place > len(scores_array):
                            result.scores = int(scores_array[-1])
                        else:
                            result.scores = int(scores_array[place - 1])
                    else:
                        result.scores = 0
                elif scores_type == 'formula':
                    time_value = result.get_result_otime().to_msec()
                    leader_time_value = ScoreCalculation.get_leader_time(result).to_msec()

                    time_phrase = 'time'
                    leader_time_phrase = 'leader'
                    expr = str(obj.get_setting('scores_formula', '0'))
                    expr = expr.replace(time_phrase, str(time_value))
                    expr = expr.replace(leader_time_phrase, str(leader_time_value))
                    value = eval(expr)
                    value = max(round(value), 0)
                    result.scores = value

    @staticmethod
    def get_leader_time(result):
        # find leader time in group
        if result and isinstance(result, Result):
            if result.person and result.person.group:
                group = result.person.group
                results = ResultCalculation(race()).get_group_finishes(group)
                best_time = None
                for cur_result in results:
                    assert isinstance(cur_result, Result)
                    if race().get_type(group) == RaceType.RELAY:
                        cur_time = get_team_result(result.person)
                    else:
                        cur_time = cur_result.get_result_otime()
                    if not best_time or cur_time < best_time:
                        best_time = cur_time
                return best_time
        return None

    @staticmethod
    def get_group_team_results(group, team):
        ret = []
        for result in race().results:
            if result.person and result.person.group == group:
                if result.person.organization == team:
                    ret.append(result)
        return ret

    @staticmethod
    def get_group_region_results(group, region):
        ret = []
        for result in race().results:
            if result.person and result.person.group == group:
                if ScoreCalculation.get_region_for_organization(result.person.organization) == region:
                    ret.append(result)
        return ret

    @staticmethod
    def get_team_results_data():
        ret = {}
        data = []
        for group in race().groups:

            group_teams = []

            team_group_mode = race().get_setting('team_group_mode', 'organization')

            if team_group_mode == 'organization':
                # organization grouping
                for team in race().organizations:
                    results = ScoreCalculation.get_group_team_results(group, team)
                    if results:
                        results = sorted(results, reverse=True, key=lambda item: item.scores)

                        # apply limit
                        limit = race().get_setting('team_qty', 0)
                        if len(results) > limit > 0:
                            results = results[:limit]

                    sum_scores = 0

                    for result in results:
                        sum_scores += result.scores

                    group_teams.append({
                        'name': team.name,
                        'member_qty': len(results),
                        'scores': sum_scores
                    })
            else:
                # region grouping
                for team in ScoreCalculation.get_all_regions():
                    results = ScoreCalculation.get_group_region_results(group, team)
                    if results:
                        results = sorted(results, reverse=True, key=lambda item: item.scores)

                        # apply limit
                        limit = race().get_setting('team_qty', 0)
                        if len(results) > limit > 0:
                            results = results[:limit]

                    sum_scores = 0

                    for result in results:
                        sum_scores += result.scores

                    group_teams.append({
                        'name': team,
                        'member_qty': len(results),
                        'scores': sum_scores
                    })
            data.append({
                'name': group.name,
                'teams': group_teams,
            })
        ret['groups'] = data
        ret['race'] = race().to_dict()
        return ret

    @staticmethod
    def get_region_for_organization(org):
        if org:
            assert isinstance(org, Organization)
            if org.address:
                if org.address.state:
                    return org.address.state
        return None

    @staticmethod
    def get_all_regions():
        ret = []
        for i in race().organizations:
            region = ScoreCalculation.get_region_for_organization(i)
            if region and not region in ret:
                ret.append(region)
        return ret
