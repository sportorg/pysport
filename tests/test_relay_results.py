import pytest

from sportorg.common.otime import OTime
from sportorg.models.memory import (
    Group,
    Organization,
    Person,
    Race,
    RaceType,
    RelayTeam,
    ResultManual,
    ResultStatus,
    create,
    new_event,
    race,
)
from sportorg.models.result.result_tools import recalculate_results


@pytest.fixture
def prepare_race():
    new_event([create(Race)])
    race().add_new_group(append_to_race=True)
    get_group().name = "Group1"
    get_group().set_type(RaceType.RELAY)
    race().data.relay_leg_count = 3


@pytest.fixture
def create_single_team(prepare_race):
    create_relay_team("Team1", 1, 3, 30)
    recalculate_results(recheck_results=False)


def test_create_relay_data(create_single_team):
    assert len(race().relay_teams) == 1
    team = race().relay_teams[0]
    assert team.bib_number == 1
    assert team.description == "Team1"
    assert team.place == 1
    assert team.order == 1
    assert team.get_is_all_legs_finished()
    assert team.get_is_status_ok()
    assert team.get_is_all_legs_finished()
    assert team.get_is_team_placed()


@pytest.fixture
def create_multiple_teams(prepare_race):
    # 1. Team with best result
    create_relay_team("Team1", 1, 3, 30)

    # 2. Team from same organization
    create_relay_team("Team1", 2, 3, 35)

    # 3. Team with not best result
    create_relay_team("Team3", 3, 3, 40)

    # 4. Team with atheletes from different organizations
    team = create_relay_team("Team4", 4, 3, 45)
    team.get_leg(1).person.organization = get_org_by_name("Team3")

    # 5. Team from same organization
    create_relay_team("Team3", 5, 3, 50)

    # 6. Team from same organization
    create_relay_team("Team1", 6, 3, 55)

    # 7. Team with worst result
    create_relay_team("Team7", 7, 3, 100)

    # 8. Team is out of competition
    team = create_relay_team("Team8", 8, 3, 50)
    team.get_leg(3).person.is_out_of_competition = True

    # 9. Incomplete team with more legs with better result
    create_relay_team("Team9", 9, 2, 30)

    # 10. Team with not all legs finished
    team = create_relay_team("Team10", 10, 2, 35)
    person = team.get_leg(2).person
    team_name = person.organization.name
    create_person("P3_" + team_name, team_name, person.bib + 1000)

    # 12. Icomplete team with more legs with worse result
    create_relay_team("Team12", 12, 2, 40)

    # 13. Team with fewer legs
    create_relay_team("Team13", 13, 1, 30)

    # 11. Not started team
    team = create_relay_team("Team11", 11, 3, 20)
    team.get_leg(1).result.status = ResultStatus.DID_NOT_START
    team.get_leg(2).result.status = ResultStatus.DID_NOT_START
    team.get_leg(3).result.status = ResultStatus.DID_NOT_START

    # 7.2.4.1.1. Общий принцип
    # Последовательность снятых полных эстафетных групп

    # 14. Full team with more legs before dsq
    team = create_relay_team("Team14", 14, 3, 35)
    team.get_leg(2).result.status = ResultStatus.DISQUALIFIED
    team.get_leg(3).result.status = ResultStatus.DISQUALIFIED

    # 15. Full team with less legs before dsq
    team = create_relay_team("Team15", 15, 3, 30)
    team.get_leg(1).result.status = ResultStatus.DISQUALIFIED

    # 7.2.4.1.1. Общий принцип
    # Последовательность снятых неполных эстафетных групп с большим количеством участников

    # 16. Incomplete dsq team with better result
    team = create_relay_team("Team16", 16, 2, 35)
    team.get_leg(2).result.status = ResultStatus.DISQUALIFIED

    # 17. Full dsq team same completed legs worse result
    team = create_relay_team("Team17", 17, 2, 40)
    team.get_leg(2).result.status = ResultStatus.DISQUALIFIED
    person = team.get_leg(2).person
    team_name = person.organization.name
    create_person("P3_" + team_name, team_name, person.bib + 1000)

    # 7.2.4.1.1. Общий принцип
    # Последовательность сниятых неполных эстафетных групп с меньшим количеством участников

    # 18. Incomplete dsq team less legs
    team = create_relay_team("Team18", 18, 1, 25)
    team.get_leg(1).result.status = ResultStatus.DISQUALIFIED

    recalculate_results(recheck_results=False)


@pytest.mark.usefixtures("create_multiple_teams")
class TestRelayResults:
    """7.2.4.1.1. Общий принцип:
    * результаты полных эстафетных групп
    * (нет в п.п.7.2.4.1.1) результаты полных эстафетных групп, выступающих вне конкурса
    * результаты неполных эстафетных групп с большим количеством участников
    * результаты неполных эстафетных групп с меньшим количеством участников
    * последовательность снятых полных эстафетных групп
    * (не реализовано) последовательность снятых неполных эстафетных групп с большим количеством участников
    * (не реализовано) последовательность сниятых неполных эстафетных групп с меньшим количеством участников
    * (не реализовано) последовательность не стартовавших эстафетных групп
    """

    def test_00_results_list(self):
        expected = """Leg count: 3
Order: 1, Team1
Leg: P1_Team1, Team: Team1, Result: 00:10:00, Place: 1
Leg: P2_Team1, Team: Team1, Result: 00:20:00, Place: 1
Leg: P3_Team1, Team: Team1, Result: 00:30:00, Place: 1
Order: 2, Team1
Leg: P1_Team1, Team: Team1, Result: 00:11:40, Place: 2
Leg: P2_Team1, Team: Team1, Result: 00:23:20, Place: 2
Leg: P3_Team1, Team: Team1, Result: 00:35:00, Place: 2
Order: 3, Team3
Leg: P1_Team3, Team: Team3, Result: 00:13:20, Place: 3
Leg: P2_Team3, Team: Team3, Result: 00:26:40, Place: 3
Leg: P3_Team3, Team: Team3, Result: 00:40:00, Place: 3
Order: 4, 
Leg: P1_Team4, Team: Team3, Result: 00:15:00, Place: 4
Leg: P2_Team4, Team: Team4, Result: 00:30:00, Place: 4
Leg: P3_Team4, Team: Team4, Result: 00:45:00, Place: 4
Order: 5, Team8 (OOC)
Leg: P1_Team8, Team: Team8, Result: 00:16:40, Place: -1
Leg: P2_Team8, Team: Team8, Result: 00:33:20, Place: -1
Leg: P3_Team8, Team: Team8, Result: 00:50:00 (OOC), Place: -1
Order: 6, Team3
Leg: P1_Team3, Team: Team3, Result: 00:16:40, Place: 5
Leg: P2_Team3, Team: Team3, Result: 00:33:20, Place: 5
Leg: P3_Team3, Team: Team3, Result: 00:50:00, Place: 5
Order: 7, Team1
Leg: P1_Team1, Team: Team1, Result: 00:18:20, Place: 6
Leg: P2_Team1, Team: Team1, Result: 00:36:40, Place: 6
Leg: P3_Team1, Team: Team1, Result: 00:55:00, Place: 6
Order: 8, Team7
Leg: P1_Team7, Team: Team7, Result: 00:33:20, Place: 7
Leg: P2_Team7, Team: Team7, Result: 01:06:40, Place: 7
Leg: P3_Team7, Team: Team7, Result: 01:40:00, Place: 7
Order: 9, Team9
Leg: P1_Team9, Team: Team9, Result: 00:15:00, Place: -1
Leg: P2_Team9, Team: Team9, Result: 00:30:00, Place: -1
Order: 10, Team10
Leg: P1_Team10, Team: Team10, Result: 00:17:30, Place: -1
Leg: P2_Team10, Team: Team10, Result: 00:35:00, Place: -1
Order: 11, Team12
Leg: P1_Team12, Team: Team12, Result: 00:20:00, Place: -1
Leg: P2_Team12, Team: Team12, Result: 00:40:00, Place: -1
Order: 12, Team13
Leg: P1_Team13, Team: Team13, Result: 00:30:00, Place: -1
Order: 13, Team14
Leg: P1_Team14, Team: Team14, Result: 00:11:40, Place: -1
Leg: P2_Team14, Team: Team14, Result: DISQUALIFIED, Place: -1
Leg: P3_Team14, Team: Team14, Result: DISQUALIFIED, Place: -1
Order: 14, Team16
Leg: P1_Team16, Team: Team16, Result: 00:17:30, Place: -1
Leg: P2_Team16, Team: Team16, Result: DISQUALIFIED, Place: -1
Order: 15, Team17
Leg: P1_Team17, Team: Team17, Result: 00:20:00, Place: -1
Leg: P2_Team17, Team: Team17, Result: DISQUALIFIED, Place: -1
Order: 16, Team15
Leg: P2_Team15, Team: Team15, Result: 00:20:00, Place: -1
Leg: P3_Team15, Team: Team15, Result: 00:30:00, Place: -1
Leg: P1_Team15, Team: Team15, Result: DISQUALIFIED, Place: -1
Order: 17, Team18
Leg: P1_Team18, Team: Team18, Result: DISQUALIFIED, Place: -1
Order: 18, Team11
Leg: P1_Team11, Team: Team11, Result: DID_NOT_START, Place: -1
Leg: P2_Team11, Team: Team11, Result: DID_NOT_START, Place: -1
Leg: P3_Team11, Team: Team11, Result: DID_NOT_START, Place: -1"""
        assert make_relay_resultlist() == expected

    # Результаты полных эстафетных групп
    def test_01_team_with_best_result(self):
        team = get_team_by_order(1)
        assert team is not None
        assert team.order == 1
        assert team.place == 1
        assert team.get_leg(1).person.name == "P1_Team1"

    def test_02_team_with_same_organization(self):
        team = get_team_by_order(2)
        assert team is not None
        assert team.order == 2
        assert team.place == 2
        assert team.get_leg(1).person.name == "P1_Team1"

    def test_03_team_with_not_best_result(self):
        team = get_team_by_order(3)
        assert team is not None
        assert team.order == 3
        assert team.place == 3
        assert team.get_leg(1).person.name == "P1_Team3"

    def test_04_team_with_athletes_from_different_organizations(self):
        team = get_team_by_order(4)
        assert team is not None
        assert team.order == 4
        assert team.place == 4
        assert team.get_leg(1).person.organization.name == "Team3"
        assert team.get_leg(2).person.organization.name == "Team4"

    def test_05_team_with_out_of_competition(self):
        team = get_team_by_order(5)
        assert team is not None
        assert team.order == 5
        assert team.place == -1
        assert team.get_is_out_of_competition()
        assert team.get_leg(1).person.name == "P1_Team8"

    def test_06_team_from_same_organization(self):
        team = get_team_by_order(6)
        assert team.order == 6
        assert team.place == 5
        assert team.get_leg(1).person.organization.name == "Team3"

    def test_07_team_from_same_organization(self):
        team = get_team_by_order(7)
        assert team.get_leg(1).person.organization.name == "Team1"

    def test_08_team_with_worst_result(self):
        team = get_team_by_order(8)
        assert team is not None
        assert team.order == 8
        assert team.place == 7
        assert team.get_leg(1).person.name == "P1_Team7"

    # 7.2.4.1.1. Общий принцип
    # Результаты неполных эстафетных групп с большим количеством участников
    def test_09_incomplete_team_with_more_legs_with_better_result(self):
        team = get_team_by_order(9)
        assert team is not None
        assert team.order == 9
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team9"
        assert not team.get_is_team_placed()

    def test_10_team_with_not_all_legs_finished(self):
        team = get_team_by_order(10)
        assert team is not None
        assert team.order == 10
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team10"
        assert not team.get_is_team_placed()

    def test_11_incomplete_team_with_more_legs_with_worse_result(self):
        team = get_team_by_order(11)
        assert team is not None
        assert team.order == 11
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team12"

    # 7.2.4.1.1. Общий принцип
    # Результаты неполных эстафетных групп с меньшим количеством участников
    def test_12_team_with_fewer_legs(self):
        team = get_team_by_order(12)
        assert team is not None
        assert team.order == 12
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team13"

    # 7.2.4.1.1. Общий принцип
    # Последовательность снятых полных эстафетных групп
    def test_13_full_team_with_more_legs_before_dsq(self):
        team = get_team_by_order(13)
        assert team is not None
        assert team.order == 13
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team14"
        assert team.get_leg(1).result.status == ResultStatus.OK
        assert team.get_leg(2).result.status != ResultStatus.OK
        assert team.get_correct_lap_count() == 1
        assert not team.get_is_status_ok()
        assert not team.get_is_team_placed()

    @pytest.mark.skip(reason="Wrong order, not implemented in code")
    def test_14_full_team_with_less_legs_before_dsq(self):
        team = get_team_by_order(14)
        assert team is not None
        assert team.order == 14
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team15"
        assert team.get_leg(1).result.status != ResultStatus.OK
        assert team.get_correct_lap_count() == 0
        assert not team.get_is_status_ok()
        assert not team.get_is_team_placed()

    # 7.2.4.1.1. Общий принцип
    # Последовательность снятых неполных эстафетных групп с большим количеством участников
    @pytest.mark.skip(reason="Wrong order, not implemented in code")
    def test_15_incomplete_dsq_team_with_better_result(self):
        team = get_team_by_order(15)
        assert team is not None
        assert team.order == 15
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team16"

    @pytest.mark.skip(reason="Wrong order, not implemented in code")
    def test_16_full_dsq_team_same_completed_legs_worse_result(self):
        team = get_team_by_order(16)
        assert team is not None
        assert team.order == 16
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team17"

    # 7.2.4.1.1. Общий принцип
    # Последовательность сниятых неполных эстафетных групп с меньшим количеством участников
    @pytest.mark.skip(reason="Not implemented in code")
    def test_17_incomplete_dsq_team_with_less_legs(self):
        team = get_team_by_order(17)
        assert team is not None
        assert team.order == 17
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team18"

    # 7.2.4.1.1. Общий принцип
    # Последовательность не стартовавших эстафетных групп
    @pytest.mark.skip(reason="Not implemented in code")
    def test_18_not_started_team(self):
        team = get_team_by_order(18)
        assert team is not None
        assert team.order == 18
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team19"
        assert team.get_leg(1).result.status == ResultStatus.DID_NOT_START


@pytest.fixture
def create_multiple_teams_best_all_russian(create_multiple_teams):
    group = get_group()
    group.is_all_russian_competition = True
    group.is_best_team_placing_mode = False
    recalculate_results(recheck_results=False)


@pytest.mark.usefixtures("create_multiple_teams_best_all_russian")
class TestRelayResultsAllRussianCompetition:
    """7.2.4.1.1. Общий принцип
    Положение Минспорта, п.2.5
    Неполные эстафетные группы доформировываются из спортсменов разных
    субъектов Российской Федерации и занимают места после полных эстафетных групп"""

    def test_00_results_list(self):
        expexted = """Leg count: 3
Order: 1, Team1
Leg: P1_Team1, Team: Team1, Result: 00:10:00, Place: 1
Leg: P2_Team1, Team: Team1, Result: 00:20:00, Place: 1
Leg: P3_Team1, Team: Team1, Result: 00:30:00, Place: 1
Order: 2, Team1
Leg: P1_Team1, Team: Team1, Result: 00:11:40, Place: 2
Leg: P2_Team1, Team: Team1, Result: 00:23:20, Place: 2
Leg: P3_Team1, Team: Team1, Result: 00:35:00, Place: 2
Order: 3, Team3
Leg: P1_Team3, Team: Team3, Result: 00:13:20, Place: 3
Leg: P2_Team3, Team: Team3, Result: 00:26:40, Place: 3
Leg: P3_Team3, Team: Team3, Result: 00:40:00, Place: 3
Order: 4, Team3
Leg: P1_Team3, Team: Team3, Result: 00:16:40, Place: 4
Leg: P2_Team3, Team: Team3, Result: 00:33:20, Place: 4
Leg: P3_Team3, Team: Team3, Result: 00:50:00, Place: 4
Order: 5, Team1
Leg: P1_Team1, Team: Team1, Result: 00:18:20, Place: 5
Leg: P2_Team1, Team: Team1, Result: 00:36:40, Place: 5
Leg: P3_Team1, Team: Team1, Result: 00:55:00, Place: 5
Order: 6, Team7
Leg: P1_Team7, Team: Team7, Result: 00:33:20, Place: 6
Leg: P2_Team7, Team: Team7, Result: 01:06:40, Place: 6
Leg: P3_Team7, Team: Team7, Result: 01:40:00, Place: 6
Order: 7, 
Leg: P1_Team4, Team: Team3, Result: 00:15:00, Place: 7
Leg: P2_Team4, Team: Team4, Result: 00:30:00, Place: 7
Leg: P3_Team4, Team: Team4, Result: 00:45:00, Place: 7
Order: 8, Team8 (OOC)
Leg: P1_Team8, Team: Team8, Result: 00:16:40, Place: -1
Leg: P2_Team8, Team: Team8, Result: 00:33:20, Place: -1
Leg: P3_Team8, Team: Team8, Result: 00:50:00 (OOC), Place: -1
Order: 9, Team9
Leg: P1_Team9, Team: Team9, Result: 00:15:00, Place: -1
Leg: P2_Team9, Team: Team9, Result: 00:30:00, Place: -1
Order: 10, Team10
Leg: P1_Team10, Team: Team10, Result: 00:17:30, Place: -1
Leg: P2_Team10, Team: Team10, Result: 00:35:00, Place: -1
Order: 11, Team12
Leg: P1_Team12, Team: Team12, Result: 00:20:00, Place: -1
Leg: P2_Team12, Team: Team12, Result: 00:40:00, Place: -1
Order: 12, Team13
Leg: P1_Team13, Team: Team13, Result: 00:30:00, Place: -1
Order: 13, Team14
Leg: P1_Team14, Team: Team14, Result: 00:11:40, Place: -1
Leg: P2_Team14, Team: Team14, Result: DISQUALIFIED, Place: -1
Leg: P3_Team14, Team: Team14, Result: DISQUALIFIED, Place: -1
Order: 14, Team16
Leg: P1_Team16, Team: Team16, Result: 00:17:30, Place: -1
Leg: P2_Team16, Team: Team16, Result: DISQUALIFIED, Place: -1
Order: 15, Team17
Leg: P1_Team17, Team: Team17, Result: 00:20:00, Place: -1
Leg: P2_Team17, Team: Team17, Result: DISQUALIFIED, Place: -1
Order: 16, Team15
Leg: P2_Team15, Team: Team15, Result: 00:20:00, Place: -1
Leg: P3_Team15, Team: Team15, Result: 00:30:00, Place: -1
Leg: P1_Team15, Team: Team15, Result: DISQUALIFIED, Place: -1
Order: 17, Team18
Leg: P1_Team18, Team: Team18, Result: DISQUALIFIED, Place: -1
Order: 18, Team11
Leg: P1_Team11, Team: Team11, Result: DID_NOT_START, Place: -1
Leg: P2_Team11, Team: Team11, Result: DID_NOT_START, Place: -1
Leg: P3_Team11, Team: Team11, Result: DID_NOT_START, Place: -1"""
        assert make_relay_resultlist() == expexted

    # Результаты полных эстафетных групп
    def test_01_team_with_best_result(self):
        team = get_team_by_order(1)
        assert team is not None
        assert team.order == 1
        assert team.place == 1
        assert team.get_leg(1).person.name == "P1_Team1"

    def test_02_team_with_same_organization(self):
        team = get_team_by_order(2)
        assert team is not None
        assert team.order == 2
        assert team.place == 2
        assert team.get_leg(1).person.name == "P1_Team1"

    def test_03_team_with_not_best_result(self):
        team = get_team_by_order(3)
        assert team is not None
        assert team.order == 3
        assert team.place == 3
        assert team.get_leg(1).person.name == "P1_Team3"

    def test_04_team_from_same_organization(self):
        team = get_team_by_order(4)
        assert team.order == 4
        assert team.place == 4
        assert team.get_leg(1).person.organization.name == "Team3"

    def test_05_team_from_same_organization(self):
        team = get_team_by_order(5)
        assert team.order == 5
        assert team.place == 5
        assert team.get_leg(1).person.organization.name == "Team1"

    def test_06_team_with_worst_result(self):
        team = get_team_by_order(6)
        assert team is not None
        assert team.order == 6
        assert team.place == 6
        assert team.get_leg(1).person.name == "P1_Team7"

    # Положение Минспорта, п.2.5: Эстафетные группы, состоящие из спортсменов спортивных
    # сборных команд разных субъектов Российской Федерации <...> занимают места после полных
    # эстафетных групп сформированных из спортсменов одного субъекта Российской Федерации
    def test_07_team_with_athletes_from_different_organizations(self):
        team = get_team_by_order(7)
        assert team is not None
        assert team.order == 7
        assert team.place == 7
        assert team.get_leg(1).person.organization.name == "Team3"
        assert team.get_leg(2).person.organization.name == "Team4"

    # This team is out of competition
    def test_08_team_with_out_of_competition(self):
        team = get_team_by_order(8)
        assert team is not None
        assert team.order == 8
        assert team.place == -1
        assert team.get_is_out_of_competition()
        assert team.get_leg(1).person.name == "P1_Team8"

    # 7.2.4.1.1. Общий принцип
    # Результаты неполных эстафетных групп с большим количеством участников
    def test_09_incomplete_team_with_more_legs_with_better_result(self):
        team = get_team_by_order(9)
        assert team is not None
        assert team.order == 9
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team9"
        assert not team.get_is_team_placed()

    def test_10_team_with_not_all_legs_finished(self):
        team = get_team_by_order(10)
        assert team is not None
        assert team.order == 10
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team10"
        assert not team.get_is_team_placed()

    def test_11_incomplete_team_with_more_legs_with_worse_result(self):
        team = get_team_by_order(11)
        assert team is not None
        assert team.order == 11
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team12"

    # 7.2.4.1.1. Общий принцип
    # Результаты неполных эстафетных групп с меньшим количеством участников
    def test_12_team_with_fewer_legs(self):
        team = get_team_by_order(12)
        assert team is not None
        assert team.order == 12
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team13"

    # 7.2.4.1.1. Общий принцип
    # Последовательность снятых полных эстафетных групп
    def test_13_full_team_with_more_legs_before_dsq(self):
        team = get_team_by_order(13)
        assert team is not None
        assert team.order == 13
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team14"
        assert team.get_leg(1).result.status == ResultStatus.OK
        assert team.get_leg(2).result.status != ResultStatus.OK
        assert team.get_correct_lap_count() == 1
        assert not team.get_is_status_ok()
        assert not team.get_is_team_placed()

    @pytest.mark.skip(reason="Wrong order, not implemented in code")
    def test_14_full_team_with_less_legs_before_dsq(self):
        team = get_team_by_order(14)
        assert team is not None
        assert team.order == 14
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team15"
        assert team.get_leg(1).result.status != ResultStatus.OK
        assert team.get_correct_lap_count() == 0
        assert not team.get_is_status_ok()
        assert not team.get_is_team_placed()

    # 7.2.4.1.1. Общий принцип
    # Последовательность снятых неполных эстафетных групп с большим количеством участников
    @pytest.mark.skip(reason="Wrong order, not implemented in code")
    def test_15_incomplete_dsq_team_with_better_result(self):
        team = get_team_by_order(15)
        assert team is not None
        assert team.order == 15
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team16"

    @pytest.mark.skip(reason="Wrong order, not implemented in code")
    def test_16_full_dsq_team_same_completed_legs_worse_result(self):
        team = get_team_by_order(16)
        assert team is not None
        assert team.order == 16
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team17"

    # 7.2.4.1.1. Общий принцип
    # Последовательность сниятых неполных эстафетных групп с меньшим количеством участников
    @pytest.mark.skip(reason="Not implemented in code")
    def test_17_incomplete_dsq_team_with_less_legs(self):
        team = get_team_by_order(17)
        assert team is not None
        assert team.order == 17
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team18"

    # 7.2.4.1.1. Общий принцип
    # Последовательность не стартовавших эстафетных групп
    @pytest.mark.skip(reason="Not implemented in code")
    def test_18_not_started_team(self):
        team = get_team_by_order(18)
        assert team is not None
        assert team.order == 18
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team11"
        assert team.get_leg(1).result.status == ResultStatus.DID_NOT_START


def create_relay_team(
    team_name: str, team_bib: int, num_runners: int, result_minutes: int
) -> RelayTeam:
    team = RelayTeam(race())
    team.bib_number = team_bib
    team.group = get_group()
    leg_result_msec = result_minutes * 60 * 1000 // num_runners
    leg_start_msec = 0

    for leg_no in range(1, num_runners + 1):
        person_bib = leg_no * 1000 + team_bib
        person_name = "P" + str(leg_no) + "_" + team_name
        person = create_person(person_name, team_name, person_bib)

        person.start_time = OTime(msec=leg_start_msec)
        result = create_result(person, leg_start_msec, leg_result_msec)

        team.add_result(result)
        leg_start_msec += leg_result_msec

    return team


def create_person(name: str, org_name: str, bib: int = 0) -> Person:
    person = Person()
    person.name = name
    person.group = get_group()
    person.set_bib(bib)
    person.organization = get_org_by_name(org_name)

    race().add_person(person)
    return person


def create_result(
    person: Person,
    start_msec: int,
    leg_time_msec: int,
    status: ResultStatus = ResultStatus.OK,
) -> ResultManual:
    result = ResultManual()
    result.person = person
    result.bib = person.bib
    result.start_time = OTime(msec=start_msec)
    result.finish_time = OTime(msec=start_msec + leg_time_msec)
    result.status = status
    race().add_result(result)
    return result


def get_group() -> Group:
    return race().groups[0]


def get_org_by_name(org_name: str) -> Organization:
    org = race().find_organization(org_name)
    if not org:
        org = race().add_new_organization(append_to_race=True)
        org.name = org_name
    return org


def get_team_by_order(order: int) -> RelayTeam:
    for team in race().relay_teams:
        if team.order == order:
            return team
    return None


@pytest.fixture
def create_multiple_teams_best_team_placing(create_multiple_teams):
    group = get_group()
    group.is_all_russian_competition = True
    group.is_best_team_placing_mode = True
    recalculate_results(recheck_results=False)


@pytest.mark.usefixtures("create_multiple_teams_best_team_placing")
class TestRelayResultsBestTeamPlacing:
    """7.2.4.1.2. Международный принцип, Положение Минспорта, п.2.5
    Результаты лучших полных эстафетных групп (по одной эстафетной группе от спортивной
    сборной команды). Неполные эстафетные группы доформировываются из спортсменов разных
    субъектов Российской Федерации и занимают места после полных эстафетных групп"""

    def test_00_results_list(self):
        expexted = """Leg count: 3
Order: 1, Team1
Leg: P1_Team1, Team: Team1, Result: 00:10:00, Place: 1
Leg: P2_Team1, Team: Team1, Result: 00:20:00, Place: 1
Leg: P3_Team1, Team: Team1, Result: 00:30:00, Place: 1
Order: 2, Team3
Leg: P1_Team3, Team: Team3, Result: 00:13:20, Place: 2
Leg: P2_Team3, Team: Team3, Result: 00:26:40, Place: 2
Leg: P3_Team3, Team: Team3, Result: 00:40:00, Place: 2
Order: 3, Team7
Leg: P1_Team7, Team: Team7, Result: 00:33:20, Place: 3
Leg: P2_Team7, Team: Team7, Result: 01:06:40, Place: 3
Leg: P3_Team7, Team: Team7, Result: 01:40:00, Place: 3
Order: 4, Team1
Leg: P1_Team1, Team: Team1, Result: 00:11:40, Place: 4
Leg: P2_Team1, Team: Team1, Result: 00:23:20, Place: 4
Leg: P3_Team1, Team: Team1, Result: 00:35:00, Place: 4
Order: 5, Team3
Leg: P1_Team3, Team: Team3, Result: 00:16:40, Place: 5
Leg: P2_Team3, Team: Team3, Result: 00:33:20, Place: 5
Leg: P3_Team3, Team: Team3, Result: 00:50:00, Place: 5
Order: 6, Team1
Leg: P1_Team1, Team: Team1, Result: 00:18:20, Place: 6
Leg: P2_Team1, Team: Team1, Result: 00:36:40, Place: 6
Leg: P3_Team1, Team: Team1, Result: 00:55:00, Place: 6
Order: 7, 
Leg: P1_Team4, Team: Team3, Result: 00:15:00, Place: 7
Leg: P2_Team4, Team: Team4, Result: 00:30:00, Place: 7
Leg: P3_Team4, Team: Team4, Result: 00:45:00, Place: 7
Order: 8, Team8 (OOC)
Leg: P1_Team8, Team: Team8, Result: 00:16:40, Place: -1
Leg: P2_Team8, Team: Team8, Result: 00:33:20, Place: -1
Leg: P3_Team8, Team: Team8, Result: 00:50:00 (OOC), Place: -1
Order: 9, Team9
Leg: P1_Team9, Team: Team9, Result: 00:15:00, Place: -1
Leg: P2_Team9, Team: Team9, Result: 00:30:00, Place: -1
Order: 10, Team10
Leg: P1_Team10, Team: Team10, Result: 00:17:30, Place: -1
Leg: P2_Team10, Team: Team10, Result: 00:35:00, Place: -1
Order: 11, Team12
Leg: P1_Team12, Team: Team12, Result: 00:20:00, Place: -1
Leg: P2_Team12, Team: Team12, Result: 00:40:00, Place: -1
Order: 12, Team13
Leg: P1_Team13, Team: Team13, Result: 00:30:00, Place: -1
Order: 13, Team14
Leg: P1_Team14, Team: Team14, Result: 00:11:40, Place: -1
Leg: P2_Team14, Team: Team14, Result: DISQUALIFIED, Place: -1
Leg: P3_Team14, Team: Team14, Result: DISQUALIFIED, Place: -1
Order: 14, Team16
Leg: P1_Team16, Team: Team16, Result: 00:17:30, Place: -1
Leg: P2_Team16, Team: Team16, Result: DISQUALIFIED, Place: -1
Order: 15, Team17
Leg: P1_Team17, Team: Team17, Result: 00:20:00, Place: -1
Leg: P2_Team17, Team: Team17, Result: DISQUALIFIED, Place: -1
Order: 16, Team15
Leg: P2_Team15, Team: Team15, Result: 00:20:00, Place: -1
Leg: P3_Team15, Team: Team15, Result: 00:30:00, Place: -1
Leg: P1_Team15, Team: Team15, Result: DISQUALIFIED, Place: -1
Order: 17, Team18
Leg: P1_Team18, Team: Team18, Result: DISQUALIFIED, Place: -1
Order: 18, Team11
Leg: P1_Team11, Team: Team11, Result: DID_NOT_START, Place: -1
Leg: P2_Team11, Team: Team11, Result: DID_NOT_START, Place: -1
Leg: P3_Team11, Team: Team11, Result: DID_NOT_START, Place: -1"""
        assert make_relay_resultlist() == expexted

    def test_01_team_with_best_result(self):
        team = get_team_by_order(1)
        assert team is not None
        assert team.order == 1
        assert team.place == 1
        assert team.get_leg(1).person.name == "P1_Team1"

    def test_02_team_with_not_best_result(self):
        team = get_team_by_order(2)
        assert team is not None
        assert team.order == 2
        assert team.place == 2
        assert team.get_leg(1).person.name == "P1_Team3"

    def test_03_team_with_worst_result(self):
        team = get_team_by_order(3)
        assert team is not None
        assert team.order == 3
        assert team.place == 3
        assert team.get_leg(1).person.name == "P1_Team7"

    # 7.2.4.1.2. Международный принцип
    # Результаты полных эстафетных групп не включенных в протокол результатов
    # по предыдущему подпункту, пункта 7.2.4.1.2
    def test_04_team_with_same_organization(self):
        team = get_team_by_order(4)
        assert team is not None
        assert team.order == 4
        assert team.place == 4
        assert team.get_leg(1).person.name == "P1_Team1"

    def test_05_team_from_same_organization(self):
        team = get_team_by_order(5)
        assert team.get_leg(1).person.organization.name == "Team3"

    def test_06_team_from_same_organization(self):
        team = get_team_by_order(6)
        assert team.get_leg(1).person.organization.name == "Team1"

    def test_07_team_with_athletes_from_different_organizations(self):
        team = get_team_by_order(7)
        assert team is not None
        assert team.order == 7
        assert team.place == 7
        assert team.get_leg(1).person.organization.name == "Team3"
        assert team.get_leg(2).person.organization.name == "Team4"

    # This team is out of competition
    def test_08_team_with_out_of_competition(self):
        team = get_team_by_order(8)
        assert team is not None
        assert team.order == 8
        assert team.place == -1
        assert team.get_is_out_of_competition()
        assert team.get_leg(1).person.name == "P1_Team8"

    # 7.2.4.1.2. Международный принцип
    # Результаты неполных эстафетных групп с большим количеством участников
    def test_09_incomplete_team_with_more_legs_with_better_result(self):
        team = get_team_by_order(9)
        assert team is not None
        assert team.order == 9
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team9"
        assert not team.get_is_team_placed()

    def test_10_team_with_not_all_legs_finished(self):
        team = get_team_by_order(10)
        assert team is not None
        assert team.order == 10
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team10"
        assert not team.get_is_team_placed()

    def test_11_incomplete_team_with_more_legs_with_worse_result(self):
        team = get_team_by_order(11)
        assert team is not None
        assert team.order == 11
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team12"

    # 7.2.4.1.2. Международный принцип
    # Результаты неполных эстафетных групп с меньшим количеством участников
    def test_12_team_with_fewer_legs(self):
        team = get_team_by_order(12)
        assert team is not None
        assert team.order == 12
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team13"

    # 7.2.4.1.2. Международный принцип
    # Последовательность снятых полных эстафетных групп
    def test_13_full_team_with_more_legs_before_dsq(self):
        team = get_team_by_order(13)
        assert team is not None
        assert team.order == 13
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team14"
        assert team.get_leg(1).result.status == ResultStatus.OK
        assert team.get_leg(2).result.status != ResultStatus.OK
        assert team.get_correct_lap_count() == 1
        assert not team.get_is_status_ok()
        assert not team.get_is_team_placed()

    @pytest.mark.skip(reason="Wrong order, not implemented in code")
    def test_14_full_team_with_less_legs_before_dsq(self):
        team = get_team_by_order(14)
        assert team is not None
        assert team.order == 14
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team15"
        assert team.get_leg(1).result.status != ResultStatus.OK
        assert team.get_correct_lap_count() == 0
        assert not team.get_is_status_ok()
        assert not team.get_is_team_placed()

    # 7.2.4.1.2. Международный принцип
    # Последовательность снятых неполных эстафетных групп с большим количеством участников
    @pytest.mark.skip(reason="Wrong order, not implemented in code")
    def test_15_incomplete_dsq_team_with_better_result(self):
        team = get_team_by_order(15)
        assert team is not None
        assert team.order == 15
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team16"

    @pytest.mark.skip(reason="Wrong order, not implemented in code")
    def test_16_full_dsq_team_same_completed_legs_worse_result(self):
        team = get_team_by_order(16)
        assert team is not None
        assert team.order == 16
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team17"

    # 7.2.4.1.2. Международный принцип
    # Последовательность сниятых неполных эстафетных групп с меньшим количеством участников
    @pytest.mark.skip(reason="Not implemented in code")
    def test_17_incomplete_dsq_team_with_less_legs(self):
        team = get_team_by_order(17)
        assert team is not None
        assert team.order == 17
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team18"

    # 7.2.4.1.2. Международный принцип
    # Последовательность не стартовавших эстафетных групп
    @pytest.mark.skip(reason="Not implemented in code")
    def test_18_not_started_team(self):
        team = get_team_by_order(18)
        assert team is not None
        assert team.order == 18
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team11"
        assert team.get_leg(1).result.status == ResultStatus.DID_NOT_START


def create_relay_team(
    team_name: str, team_bib: int, num_runners: int, result_minutes: int
) -> RelayTeam:
    team = RelayTeam(race())
    team.bib_number = team_bib
    team.group = get_group()
    leg_result_msec = result_minutes * 60 * 1000 // num_runners
    leg_start_msec = 0

    for leg_no in range(1, num_runners + 1):
        person_bib = leg_no * 1000 + team_bib
        person_name = "P" + str(leg_no) + "_" + team_name
        person = create_person(person_name, team_name, person_bib)

        person.start_time = OTime(msec=leg_start_msec)
        result = create_result(person, leg_start_msec, leg_result_msec)

        team.add_result(result)
        leg_start_msec += leg_result_msec

    return team


def create_person(name: str, org_name: str, bib: int = 0) -> Person:
    person = Person()
    person.name = name
    person.group = get_group()
    person.set_bib(bib)
    person.organization = get_org_by_name(org_name)

    race().add_person(person)
    return person


def create_result(
    person: Person,
    start_msec: int,
    leg_time_msec: int,
    status: ResultStatus = ResultStatus.OK,
) -> ResultManual:
    result = ResultManual()
    result.person = person
    result.bib = person.bib
    result.start_time = OTime(msec=start_msec)
    result.finish_time = OTime(msec=start_msec + leg_time_msec)
    result.status = status
    race().add_result(result)
    return result


def get_group() -> Group:
    return race().groups[0]


def get_org_by_name(org_name: str) -> Organization:
    org = race().find_organization(org_name)
    if not org:
        org = race().add_new_organization(append_to_race=True)
        org.name = org_name
    return org


def get_team_by_order(order: int) -> RelayTeam:
    for team in race().relay_teams:
        if team.order == order:
            return team
    return None


def print_teams(file_name=None):
    """Prints the result list to a file or console for debugging purposes."""
    result_list = make_relay_resultlist()
    if file_name:
        with open(file_name, "w", encoding="utf-8") as f:
            f.writelines(result_list)
    else:
        print(result_list)


def make_relay_resultlist():
    lines = []
    lines.append("Leg count: {}".format(race().data.relay_leg_count))
    teams = sorted(race().relay_teams, key=lambda t: t.order)
    for team in teams:
        team_name = team.description
        if team.get_is_out_of_competition():
            team_name += " (OOC)"
        lines.append("Order: {}, {}".format(team.order, team_name))
        for leg in team.legs:
            if leg.result.status == ResultStatus.OK:
                result = leg.result.get_result()
            else:
                result = leg.result.status.name
            if leg.person.is_out_of_competition:
                result += " (OOC)"
            lines.append(
                "Leg: {}, Team: {}, Result: {}, Place: {}".format(
                    leg.person.name,
                    leg.person.organization,
                    result,
                    team.place,
                )
            )

    return "\n".join(lines)
