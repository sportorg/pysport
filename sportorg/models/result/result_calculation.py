from typing import Dict, List

from sportorg import settings
from sportorg.common.otime import OTime
from sportorg.models.constant import RankingTable
from sportorg.models.memory import (
    Group,
    Qualification,
    Race,
    RaceType,
    RelayTeam,
    Result,
    ResultStatus,
    find,
)


class ResultCalculation:
    def __init__(self, r: Race):
        self.race = r
        self._group_finishes = {}
        self._group_persons = {}

    def process_results(self):
        self.race.relay_teams.clear()
        self.race.result_index = {}
        for person in self.race.persons:
            person.result_count = 0
            if person.start_time and person.group:
                if person.group.pursuit_start_time != OTime():
                    person.group.pursuit_start_time = min(
                        person.start_time, person.group.pursuit_start_time
                    )
                else:
                    person.group.pursuit_start_time = person.start_time

        for result in self.race.results:
            if result.person:
                result.person.result_count += 1
        for i in self.race.groups:
            if not self.race.get_type(i) == RaceType.RELAY:
                # single race
                array = self.get_group_finishes(i)
                self.set_places(array)
            else:
                # relay
                new_relays = self.process_relay_results(i)
                for a in new_relays:
                    self.race.relay_teams.append(a)
            self.set_rank(i)

    def get_group_finishes(self, group: Group) -> Result:
        if group in self._group_finishes:
            return self._group_finishes[group]
        ret = []
        for i in self.race.results:
            person = i.person
            if person:
                if person.group is group:
                    ret.append(i)
        ret.sort()
        group.count_finished = len(ret)
        self._group_finishes[group] = ret
        return ret

    def get_group_persons(self, group):
        if group in self._group_persons:
            return self._group_persons[group]
        ret = []
        for i in self.race.persons:
            person = i
            if person.group is group:
                ret.append(i)
        group.count_person = len(ret)
        self._group_persons[group] = ret
        return ret

    def set_places(self, array):
        is_rogaine = self.race.get_setting("result_processing_mode", "time") == "scores"
        is_ardf = self.race.get_setting("result_processing_mode", "time") == "ardf"
        current_place = 1
        last_place = 1
        last_result = 0
        for i in range(len(array)):
            res = array[i]

            res.place = -1
            # give place only if status = OK
            if res.is_status_ok():
                current_result = res.get_result_otime()
                res.diff = current_result - array[0].get_result_otime()
                if is_rogaine:
                    res.diff_scores = array[0].rogaine_score - res.rogaine_score
                elif is_ardf:
                    res.diff_scores = array[0].scores_ardf - res.scores_ardf

                # skip if out of competition
                if res.person.is_out_of_competition:
                    res.place = -1
                    continue

                # the same place processing
                if current_place == 1 or current_result != last_result:
                    # result differs from previous - give next place
                    last_result = current_result
                    last_place = current_place

                res.place = last_place
                current_place += 1
            else:
                res.current_result = res.get_result()

    def process_relay_results(self, group: Group) -> List[RelayTeam]:
        results = self.get_group_finishes(group)

        relay_teams: Dict[str, RelayTeam] = {}
        for res in results:
            bib = res.person.bib

            team_number = bib % 1000
            if str(team_number) not in relay_teams:
                new_team = RelayTeam(self.race)
                new_team.group = group
                new_team.bib_number = team_number
                if res.person.organization:
                    new_team.description = res.person.organization.name
                relay_teams[str(team_number)] = new_team

            team = relay_teams[str(team_number)]
            team.add_result(res)
        teams_sorted = sorted(relay_teams.values())

        if group.is_all_russian_competition:
            teams_sorted = self.sort_relay_all_russian_competition(teams_sorted)

        place = 1  # place to show
        order = 1  # order for templates
        for cur_team in teams_sorted:
            if not cur_team.get_is_team_placed():
                cur_team.set_place(-1)
            else:
                cur_team.set_place(place)
                place += 1

            cur_team.set_order(order)
            order += 1

            cur_team.set_start_times()
        return relay_teams.values()

    def sort_relay_all_russian_competition(
        self, teams_sorted_by_result: List[RelayTeam]
    ):
        """If a Federation is represented by more than one team in a relay class,
        one team with the best result from each Federation shall be placed first

        The remaining teams from the federations are placed next

        Teams composed of competitors from more than one Federation are considered
        if they are to be out of competition. Teams participating outside
        the competition are placed after the teams participating in the competition

        Teams with fewer competitors are placed next"""

        if not teams_sorted_by_result:
            return teams_sorted_by_result

        processed_teams = set()
        sorted_teams: List[RelayTeam] = []
        skipped_second_teams: List[RelayTeam] = []
        skipped_mixed_teams: List[RelayTeam] = []
        skipped_out_of_competition_teams: List[RelayTeam] = []
        best_team = teams_sorted_by_result[0]
        is_all_russian_competition = best_team.group.is_all_russian_competition
        is_best_team_placing_mode = best_team.group.is_best_team_placing_mode
        is_placed_flag = best_team.get_is_team_placed()

        for team in teams_sorted_by_result:
            if is_placed_flag and not team.get_is_team_placed(
                place_out_of_competition=True
            ):
                is_placed_flag = False
                sorted_teams.extend(skipped_second_teams)
                sorted_teams.extend(skipped_mixed_teams)
                sorted_teams.extend(skipped_out_of_competition_teams)
            if is_placed_flag:
                if is_all_russian_competition and team.get_is_out_of_competition():
                    skipped_out_of_competition_teams.append(team)
                elif is_all_russian_competition and not team.description:
                    skipped_mixed_teams.append(team)
                elif (
                    is_best_team_placing_mode
                    and team.description
                    and team.description not in processed_teams
                ):
                    sorted_teams.append(team)
                    processed_teams.add(team.description)
                else:
                    skipped_second_teams.append(team)
            else:
                sorted_teams.append(team)

        return sorted_teams

    def set_rank(self, group):
        ranking = group.ranking
        results = self.get_group_finishes(group)

        # initial turning off, for disabling ranking
        for i in results:
            i.assigned_rank = Qualification.NOT_QUALIFIED

        if ranking.is_active:
            if group.is_relay():
                rank = self.get_group_rank_relay(group)
            else:
                rank = self.get_group_rank(group)
            ranking.rank_scores = rank
            if rank > 0:
                is_score_processing_mode = (
                    self.race.get_setting("result_processing_mode", "time") == "scores"
                    or self.race.get_setting("result_processing_mode", "time") == "ardf"
                )
                leader_time = OTime(0)
                leader_scores = 0
                if is_score_processing_mode:
                    results = self.get_group_finishes(group)
                    if len(results) > 0:
                        leader_result = results[0]
                        leader_scores = leader_result.scores
                else:
                    leader_time = self.get_group_leader_time(group)

                for i in ranking.rank.values():
                    if i.is_active and i.use_scores:
                        i.percent = self.get_percent_for_rank(i.qual, rank)
                        i.max_place = 0
                        if is_score_processing_mode:
                            i.min_scores = self.get_scores_for_rank(
                                leader_scores, i.qual, rank
                            )
                        else:
                            i.max_time = self.get_time_for_rank(
                                leader_time, i.qual, rank
                            )
                    else:
                        i.percent = 0

            # Rank assigning for all athletes
            for i in results:
                result_time = i.get_result_otime()
                result_scores = i.scores
                place = i.place

                if i.person.is_out_of_competition or not i.is_status_ok():
                    continue

                qual_list = sorted(
                    ranking.rank.values(),
                    reverse=True,
                    key=lambda item: item.qual.get_score(),
                )
                for j in qual_list:
                    if j.is_active:
                        if isinstance(place, int) and j.max_place >= place:
                            i.assigned_rank = j.qual
                            break
                        if j.max_time and j.max_time >= result_time:
                            i.assigned_rank = j.qual
                            break
                        if result_scores >= j.min_scores > 0:
                            i.assigned_rank = j.qual
                            break

    def get_group_leader_time(self, group):
        if self.race.get_type(group) == RaceType.RELAY:
            team_result = find(self.race.relay_teams, group=group, place=1)
            if isinstance(team_result, RelayTeam):
                leader_time = team_result.get_time()
            else:
                return OTime()
        else:
            results = self.get_group_finishes(group)
            if len(results) > 0:
                leader_result = results[0]
                leader_time = leader_result.get_result_otime()
            else:
                return OTime()
        return leader_time

    def get_group_rank(self, group):
        """
        Rank calculation, takes sums or scores from qualification of best X (default=10)
        athletes, who have OK result and are not out of competition

        :return: rank of group, -1 if we have < X (default=5) successful results
        """
        scores = []
        array = self.get_group_finishes(group)

        start_limit = settings.SETTINGS.ranking.get("start_limit", 10)
        finish_limit = settings.SETTINGS.ranking.get("finish_limit", 5)
        sum_count = settings.SETTINGS.ranking.get("sum_count", 10)
        individual_ranking_method = settings.SETTINGS.ranking.get(
            "individual_ranking_method", "best"
        )

        started_count = 0
        for i in array:
            person = i.person
            if not person.is_out_of_competition and i.status not in [
                ResultStatus.DID_NOT_START
            ]:
                started_count += 1
                if i.is_status_ok():
                    qual = person.qual
                    scores.append(qual.get_score())

        if started_count < start_limit:
            # less than X (default=10) started
            return -1

        if len(scores) < finish_limit:
            # less than X (default=5) finished and not disqualified
            return -1

        if len(scores) <= sum_count:
            # get rank sum of X (default=10) best finished
            return sum(scores)

        if individual_ranking_method == "best":
            scores = sorted(scores)
        else:
            # Use points of first N in protocol,
            # reverse list and get last values (1st place in the end)
            scores.reverse()
        return sum(scores[-sum_count:])

    def get_group_rank_relay(self, group):
        """
        Rank calculation, takes sums or scores from qualification of best X (default=10)
        athletes, who have OK result and are not out of competition

        :return: rank of group, -1 if we have < X (default=4) successful teams
        """
        teams = find(self.race.relay_teams, group=group, return_all=True)
        success_teams = []

        start_limit = settings.SETTINGS.ranking.get("start_limit_relay", 6)
        finish_limit = settings.SETTINGS.ranking.get("finish_limit_relay", 4)
        sum_count = settings.SETTINGS.ranking.get("sum_count_relay", 10)
        relay_ranking_method = settings.SETTINGS.ranking.get(
            "relay_ranking_method", "personal"
        )

        started_teams = 0
        if teams:
            for cur_team in teams:
                if cur_team.get_is_out_of_competition():
                    continue
                if not cur_team.get_is_all_legs_finished():
                    continue
                started_teams += 1
                if cur_team.get_is_status_ok():
                    success_teams.append(cur_team)

        if started_teams < start_limit:
            # less than X (default=6) teams started in relay
            return -1

        if len(success_teams) < finish_limit:
            # less than X (default=4) teams successfully finished in relay
            return -1

        if relay_ranking_method in ["personal", "first"]:
            scores = []
            for cur_team in success_teams:
                for cur_leg in cur_team.legs:
                    res = cur_leg.get_result()
                    person = res.person
                    qual = person.qual
                    scores.append(qual.get_score())

            if len(scores) <= sum_count:
                # get rank sum of X (default=10) best
                # (by qualification, ignoring places) finished
                return sum(scores)

            if relay_ranking_method == "personal":
                scores = sorted(scores)
            else:
                # get rank sum of X (default=10), taken from first in protocol teams
                scores.reverse()

            return sum(scores[-sum_count:])
        else:
            # calculate average team score and get sum of first X teams
            average_sum = 0
            for cur_team in success_teams[:sum_count]:
                team_sum = 0
                for cur_leg in cur_team.legs:
                    res = cur_leg.get_result()
                    person = res.person
                    qual = person.qual
                    team_sum += qual.get_score()
                average_sum += team_sum / len(cur_team.legs)
            return average_sum

    @staticmethod
    def get_percent_for_rank(qual, rank):
        table = RankingTable().get_qual_table(qual)

        for i in range(len(table)):
            cur_value = table[i][0]
            if cur_value <= rank:
                return table[i][1]
        return 0

    def get_time_for_rank(self, leader_time, qual, rank):
        percent = self.get_percent_for_rank(qual, rank)
        if leader_time:
            msec_new = round(leader_time.to_msec() * percent / 100)
            ret = OTime(msec=msec_new)
            return ret
        return None

    def get_scores_for_rank(self, leader_scores, qual, rank):
        percent = self.get_percent_for_rank(qual, rank)
        if leader_scores:
            ret = round(int(leader_scores) * percent / 100)
            return ret
        return 0
