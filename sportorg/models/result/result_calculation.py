import logging

from sportorg.core.otime import OTime
from sportorg.language import _
from sportorg.models.memory import race, Result, Person, Group, Qualification, RankingItem, \
    RelayTeam, RaceType, find


# FIXME: does not work sorting
class ResultCalculation(object):
    def __init__(self, r):
        self.race = r

    def process_results(self):
        logging.debug('Process results')
        self.race.relay_teams.clear()
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
            assert isinstance(i, Result)
            person = i.person
            if person:
                assert isinstance(person, Person)
                if person.group == group:
                    ret.append(i)
        ret.sort()
        group.count_finished = len(ret)
        return ret

    def get_group_persons(self, group):
        assert isinstance(group, Group)
        ret = []
        for i in self.race.persons:
            person = i
            assert isinstance(person, Person)
            if person.group == group:
                ret.append(i)
        group.count_person = len(ret)
        return ret

    def set_places(self, array):
        assert isinstance(array, list)
        current_place = 1
        last_place = 1
        last_result = 0
        for i in range(len(array)):
            res = array[i]
            assert isinstance(res, Result)

            res.place = -1
            # give place only if status = OK
            if res.is_status_ok():
                current_result = res.get_result_otime()
                res.diff = current_result - array[0].get_result_otime()

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
                assert isinstance(res, Result)
                bib = res.person.bib

                team_number = bib % 1000
                if not str(team_number) in relay_teams:
                    new_team = RelayTeam(self.race)
                    new_team.group = group
                    new_team.bib_number = team_number
                    relay_teams[str(team_number)] = new_team

                team = relay_teams[str(team_number)]
                assert isinstance(team, RelayTeam)
                team.add_result(res)
            teams_sorted = sorted(relay_teams.values())
            place = 1
            for cur_team in teams_sorted:
                cur_team.set_place(place)
                place += 1
            return relay_teams.values()

    def set_rank(self, group):
        assert isinstance(group, Group)
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
                    assert isinstance(i, RankingItem)
                    if i.is_active and i.use_scores:
                        i.max_time = self.get_time_for_rank(leader_time, i.qual, rank)
                        i.percent = self.get_percent_for_rank(i.qual, rank)

            # Rank assigning for all athletes
            for i in results:
                assert isinstance(i, Result)
                result_time = i.get_result_otime()
                place = i.place

                if i.person.is_out_of_competition or not i.is_status_ok():
                    continue

                qual_list = sorted(ranking.rank.values(), reverse=True, key=lambda item: item.qual.get_scores())
                for j in qual_list:
                    assert isinstance(j, RankingItem)
                    if j.is_active:
                        if isinstance(place, int) and j.max_place >= place:
                            i.assigned_rank = j.qual
                            break
                        if j.max_time and j.max_time >= result_time:
                            i.assigned_rank = j.qual
                            break

    def get_group_leader_time(self, group):
        if race().get_type(group) == RaceType.RELAY:
            team_result = find(race().relay_teams, group=group, place=1)
            assert isinstance(team_result, RelayTeam)
            leader_time = team_result.get_time()
        else:
            results = self.get_group_finishes(group)
            leader_result = results[0]
            leader_time = leader_result.get_result_otime()
        return leader_time

    def get_group_rank(self, group):
        """
        Rank calculation, takes sums or scores from qualification of best 10 athletes, who have OK result and not o/c
        :param group:
        :return: rank of group, -1 if we have < 10 successfull results
        """
        scores = []
        array = self.get_group_finishes(group)

        if len(array) < 10:
            # less than 10 started
            return -1

        for i in array:
            assert isinstance(i, Result)
            if i.is_status_ok():
                person = i.person
                if not person.is_out_of_competition:
                    qual = person.qual
                    scores.append(qual.get_scores())

        if len(scores) < 5:
            # less than 5 finished and not disqualified
            return -1

        if len(scores) <= 10:
            # get rank sum of 10 best finished
            return sum(scores)

        scores = sorted(scores)
        return sum(scores[-10:])

    def get_group_rank_relay(self, group):
        """
        Rank calculation, takes sums or scores from qualification of best 10 athletes, who have OK result and not o/c
        :param group:
        :return: rank of group, -1 if we have < 10 successfull results
        """
        teams = find(race().relay_teams, group=group, return_all=True)
        success_teams = []

        started_teams = 0
        if teams:
            for cur_team in teams:
                assert isinstance(cur_team, RelayTeam)
                if cur_team.get_is_out_of_competition():
                    continue
                if not cur_team.get_is_all_legs_finished():
                    continue
                started_teams += 1
                if cur_team.get_is_status_ok():
                    success_teams.append(cur_team)

        if started_teams < 6:
            # less than 6 teams started in relay
            return -1

        if len(success_teams) < 4:
            # less than 4 teams successfully finished in relay
            return -1

        scores = []
        for cur_team in success_teams:
            for cur_leg in cur_team.legs:
                res = cur_leg.get_result()
                person = res.person
                qual = person.qual
                scores.append(qual.get_scores())

        if len(scores) <= 10:
            # get rank sum of 10 best finished
            return sum(scores)

        scores = sorted(scores)
        return sum(scores[-10:])

    def get_percent_for_rank(self, qual, rank):
        table = []
        if qual == Qualification.I:
            table = [
                 (1000, 136),
                 (850, 133),
                 (750, 130),
                 (650, 127),
                 (500, 124),
                 (425, 121),
                 (375, 118),
                 (325, 115),
                 (250, 112),
                 (211, 109),
                 (185, 106),
                 (159, 103),
                 (120, 100)
            ]
        elif qual == Qualification.II:
            table = [
                 (1000, 151),
                 (850, 148),
                 (750, 145),
                 (650, 142),
                 (500, 139),
                 (425, 136),
                 (375, 133),
                 (325, 130),
                 (250, 127),
                 (211, 124),
                 (185, 121),
                 (159, 118),
                 (120, 115),
                 (102, 112),
                 (90,  109),
                 (78,  106),
                 (60,  103),
                 (51,  100)
            ]
        elif qual == Qualification.III:
            table = [
                 (1000, 169),
                 (850, 166),
                 (750, 163),
                 (650, 160),
                 (500, 157),
                 (425, 154),
                 (375, 151),
                 (325, 148),
                 (250, 145),
                 (211, 142),
                 (185, 139),
                 (159, 136),
                 (120, 133),
                 (102, 130),
                 (90,  127),
                 (78,  124),
                 (60,  121),
                 (51,  118),
                 (45,  115),
                 (39,  112),
                 (30,  109),
                 (27,  106),
                 (25,  103),
                 (23,  100)
            ]
        elif qual == Qualification.I_Y:
            table = [
                 (650, 0),
                 (500, 192),
                 (425, 188),
                 (375, 184),
                 (325, 180),
                 (250, 176),
                 (211, 172),
                 (185, 168),
                 (159, 164),
                 (120, 160),
                 (102, 156),
                 (90, 152),
                 (78, 148),
                 (60, 144),
                 (51, 140),
                 (45, 136),
                 (39, 132),
                 (30, 128),
                 (27, 124),
                 (25, 120),
                 (23, 116),
                 (20, 112),
                 (17, 108),
                 (15, 104),
                 (13, 100)
            ]
        elif qual == Qualification.II_Y:
            table = [
                 (425, 0),
                 (375, 215),
                 (325, 210),
                 (250, 205),
                 (211, 200),
                 (185, 195),
                 (159, 190),
                 (120, 185),
                 (102, 180),
                 (90, 175),
                 (78, 170),
                 (60, 165),
                 (51, 160),
                 (45, 155),
                 (39, 150),
                 (30, 145),
                 (27, 140),
                 (25, 135),
                 (23, 130),
                 (20, 125),
                 (17, 120),
                 (15, 116),
                 (13, 112),
                 (11, 108),
                 (10, 105),
                 (7, 102),
                 (5, 100)
            ]

        for i in range(len(table)):
            cur_value = table[i][0]
            if cur_value <= rank:
                return table[i][1]
        return 0

    def get_time_for_rank(self, leader_time, qual, rank):
        percent = self.get_percent_for_rank(qual, rank)
        if leader_time:
            assert isinstance(leader_time, OTime)
            msec_new = round(leader_time.to_msec() * percent / 100)
            ret = OTime(msec=msec_new)
            return ret
        return None


def get_start_list_data():
    pass


def get_splits_data():
    pass


def get_entry_statistics_data():
    pass


def get_team_statistics_data():
    pass

