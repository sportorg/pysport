import logging

from sportorg.common.otime import OTime
from sportorg.models.constant import RankingTable
from sportorg.models.memory import Group, Qualification, RaceType, RelayTeam, find
from sportorg.modules.configs.configs import Config


class ResultCalculation(object):
    def __init__(self, r):
        self.race = r

    def process_results(self):
        logging.debug('Process results')
        self.race.relay_teams.clear()
        for person in self.race.persons:
            person.result_count = 0
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

    def get_group_finishes(self, group):
        ret = []
        for i in self.race.results:
            person = i.person
            if person:
                if person.group is group:
                    ret.append(i)
        ret.sort()
        group.count_finished = len(ret)
        return ret

    def get_group_persons(self, group):
        ret = []
        for i in self.race.persons:
            person = i
            if person.group is group:
                ret.append(i)
        group.count_person = len(ret)
        return ret

    @staticmethod
    def set_places(array):
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
                res.diff_scores = array[0].scores - res.scores

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

    def process_relay_results(self, group):
        if group and isinstance(group, Group):
            results = self.get_group_finishes(group)

            relay_teams = {}
            for res in results:
                bib = res.person.bib

                team_number = bib % 1000
                if not str(team_number) in relay_teams:
                    new_team = RelayTeam(self.race)
                    new_team.group = group
                    new_team.bib_number = team_number
                    relay_teams[str(team_number)] = new_team

                team = relay_teams[str(team_number)]
                team.add_result(res)
            teams_sorted = sorted(relay_teams.values())
            place = 1
            for cur_team in teams_sorted:
                cur_team.set_place(place)
                place += 1
                cur_team.set_start_times()
            return relay_teams.values()

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
                leader_time = self.get_group_leader_time(group)
                for i in ranking.rank.values():
                    if i.is_active and i.use_scores:
                        i.max_time = self.get_time_for_rank(leader_time, i.qual, rank)
                        i.percent = self.get_percent_for_rank(i.qual, rank)
                        i.max_place = 0
                    else:
                        i.percent = 0

            # Rank assigning for all athletes
            for i in results:
                result_time = i.get_result_otime()
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
        Rank calculation, takes sums or scores from qualification of best X (default=10) athletes, who have OK result
        and are not out of competition
        :param group:
        :return: rank of group, -1 if we have < X (default=5) successfull results
        """
        scores = []
        array = self.get_group_finishes(group)

        start_limit = Config().ranking.get('start_limit', 10)
        finish_limit = Config().ranking.get('finish_limit', 5)
        sum_count = Config().ranking.get('sum_count', 10)

        if len(array) < start_limit:
            # less than X (default=10) started
            return -1

        for i in array:
            if i.is_status_ok():
                person = i.person
                if not person.is_out_of_competition:
                    qual = person.qual
                    scores.append(qual.get_score())

        if len(scores) < finish_limit:
            # less than X (default=5) finished and not disqualified
            return -1

        if len(scores) <= sum_count:
            # get rank sum of X (default=10) best finished
            return sum(scores)

        scores = sorted(scores)
        return sum(scores[-sum_count:])

    def get_group_rank_relay(self, group):
        """
        Rank calculation, takes sums or scores from qualification of best X (default=10) athletes, who have OK result
        and are not out of competition
        :param group:
        :return: rank of group, -1 if we have < X (default=4) successfull teams
        """
        teams = find(self.race.relay_teams, group=group, return_all=True)
        success_teams = []

        start_limit = Config().ranking.get('start_limit_relay', 6)
        finish_limit = Config().ranking.get('finish_limit_relay', 4)
        sum_count = Config().ranking.get('sum_count_relay', 10)
        relay_ranking_method = Config().ranking.get('relay_ranking_method', 'personal')

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

        if relay_ranking_method == 'personal':
            scores = []
            for cur_team in success_teams:
                for cur_leg in cur_team.legs:
                    res = cur_leg.get_result()
                    person = res.person
                    qual = person.qual
                    scores.append(qual.get_score())

            if len(scores) <= sum_count:
                # get rank sum of X (default=10) best finished
                return sum(scores)

            scores = sorted(scores)
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
