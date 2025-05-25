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

    # 11. Icomplete team with more legs with worse result
    create_relay_team("Team11", 11, 2, 40)

    # 12. Team with fewer legs
    create_relay_team("Team12", 12, 1, 30)

    # 7.2.4.1.1. Общий принцип
    # Последовательность снятых полных эстафетных групп

    # 13. Full team with more legs before dsq
    team = create_relay_team("Team13", 13, 3, 35)
    team.get_leg(2).result.status = ResultStatus.DISQUALIFIED
    team.get_leg(3).result.status = ResultStatus.DISQUALIFIED

    # 14. Full team with less legs before dsq
    team = create_relay_team("Team14", 14, 3, 30)
    team.get_leg(1).result.status = ResultStatus.DISQUALIFIED

    # 7.2.4.1.1. Общий принцип
    # Последовательность снятых неполных эстафетных групп с большим количеством участников

    # 15. Incomplete dsq team with better result
    team = create_relay_team("Team15", 15, 2, 35)
    team.get_leg(2).result.status = ResultStatus.DISQUALIFIED

    # 16. Full dsq team same completed legs worse result
    team = create_relay_team("Team16", 16, 2, 40)
    team.get_leg(2).result.status = ResultStatus.DISQUALIFIED
    person = team.get_leg(2).person
    team_name = person.organization.name
    create_person("P3_" + team_name, team_name, person.bib + 1000)

    # 7.2.4.1.1. Общий принцип
    # Последовательность сниятых неполных эстафетных групп с меньшим количеством участников

    # 17. Incomplete dsq team less legs
    team = create_relay_team("Team17", 17, 1, 25)
    team.get_leg(1).result.status = ResultStatus.DISQUALIFIED

    # 7.2.4.1.1. Общий принцип
    # Последовательность не стартовавших эстафетных групп

    # 18. Not started team
    team = create_relay_team("Team18", 18, 1, 20)
    team.get_leg(1).result.status = ResultStatus.DID_NOT_START

    recalculate_results(recheck_results=False)


@pytest.mark.usefixtures("create_multiple_teams")
class TestRelayResults:
    # 7.2.4.1.1. Общий принцип
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

    def test_05_team_from_same_organization(self):
        team = get_team_by_order(5)
        assert team.get_leg(1).person.organization.name == "Team3"

    def test_06_team_from_same_organization(self):
        team = get_team_by_order(6)
        assert team.get_leg(1).person.organization.name == "Team1"

    def test_07_team_with_worst_result(self):
        team = get_team_by_order(7)
        assert team is not None
        assert team.order == 7
        assert team.place == 7
        assert team.get_leg(1).person.name == "P1_Team7"

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
        assert team.place == 8
        assert team.get_leg(1).person.name == "P1_Team9"
        assert not team.get_is_team_placed()

    def test_10_team_with_not_all_legs_finished(self):
        team = get_team_by_order(10)
        assert team is not None
        assert team.order == 10
        assert team.place == 9
        assert team.get_leg(1).person.name == "P1_Team10"
        assert not team.get_is_team_placed()

    def test_11_incomplete_team_with_more_legs_with_worse_result(self):
        team = get_team_by_order(11)
        assert team is not None
        assert team.order == 11
        assert team.place == 10
        assert team.get_leg(1).person.name == "P1_Team11"

    # 7.2.4.1.1. Общий принцип
    # Результаты неполных эстафетных групп с меньшим количеством участников
    def test_12_team_with_fewer_legs(self):
        team = get_team_by_order(12)
        assert team is not None
        assert team.order == 12
        assert team.place == 11
        assert team.get_leg(1).person.name == "P1_Team12"

    # 7.2.4.1.1. Общий принцип
    # Последовательность снятых полных эстафетных групп

    def test_13_full_team_with_more_legs_before_dsq(self):
        team = get_team_by_order(13)
        assert team is not None
        assert team.order == 13
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team13"
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
        assert team.get_leg(1).person.name == "P1_Team14"
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
        assert team.get_leg(1).person.name == "P1_Team15"

    @pytest.mark.skip(reason="Wrong order, not implemented in code")
    def test_16_full_dsq_team_same_completed_legs_worse_result(self):
        team = get_team_by_order(16)
        assert team is not None
        assert team.order == 16
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team16"

    # 7.2.4.1.1. Общий принцип
    # Последовательность сниятых неполных эстафетных групп с меньшим количеством участников
    def test_17_incomplete_dsq_team_with_less_legs(self):
        team = get_team_by_order(17)
        assert team is not None
        assert team.order == 17
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team17"

    # 7.2.4.1.1. Общий принцип
    # Последовательность не стартовавших эстафетных групп
    @pytest.mark.skip(reason="Not implemented in code")
    def test_18_not_started_team(self):
        team = get_team_by_order(18)
        assert team is not None
        assert team.order == 18
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team18"
        assert team.get_leg(1).result.status == ResultStatus.DID_NOT_START


@pytest.fixture
def create_multiple_teams_best_team_placing(create_multiple_teams):
    group = get_group()
    group.is_best_team_placing_mode = True
    recalculate_results(recheck_results=False)


@pytest.mark.usefixtures("create_multiple_teams_best_team_placing")
class TestRelayResultsBestTeamPlacing:
    # 7.2.4.1.2. Международный принцип
    # Результаты лучших полных эстафетных групп (по одной эстафетной группе
    # от спортивной сборной команды)
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

    # This team is out of competition
    def test_07_team_with_athletes_from_different_organizations(self):
        team = get_team_by_order(7)
        assert team is not None
        assert team.order == 7
        assert team.place == -1
        assert team.get_leg(1).person.organization.name == "Team3"
        assert team.get_leg(2).person.organization.name == "Team4"

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
        assert team.place == 7
        assert team.get_leg(1).person.name == "P1_Team9"
        assert not team.get_is_team_placed()

    def test_10_team_with_not_all_legs_finished(self):
        team = get_team_by_order(10)
        assert team is not None
        assert team.order == 10
        assert team.place == 8
        assert team.get_leg(1).person.name == "P1_Team10"
        assert not team.get_is_team_placed()

    def test_11_incomplete_team_with_more_legs_with_worse_result(self):
        team = get_team_by_order(11)
        assert team is not None
        assert team.order == 11
        assert team.place == 9
        assert team.get_leg(1).person.name == "P1_Team11"

    # 7.2.4.1.2. Международный принцип
    # Результаты неполных эстафетных групп с меньшим количеством участников
    def test_12_team_with_fewer_legs(self):
        team = get_team_by_order(12)
        assert team is not None
        assert team.order == 12
        assert team.place == 10
        assert team.get_leg(1).person.name == "P1_Team12"

    # 7.2.4.1.2. Международный принцип
    # Последовательность снятых полных эстафетных групп
    def test_13_full_team_with_more_legs_before_dsq(self):
        team = get_team_by_order(13)
        assert team is not None
        assert team.order == 13
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team13"
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
        assert team.get_leg(1).person.name == "P1_Team14"
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
        assert team.get_leg(1).person.name == "P1_Team15"

    @pytest.mark.skip(reason="Wrong order, not implemented in code")
    def test_16_full_dsq_team_same_completed_legs_worse_result(self):
        team = get_team_by_order(16)
        assert team is not None
        assert team.order == 16
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team16"

    # 7.2.4.1.2. Международный принцип
    # Последовательность сниятых неполных эстафетных групп с меньшим количеством участников
    def test_17_incomplete_dsq_team_with_less_legs(self):
        team = get_team_by_order(17)
        assert team is not None
        assert team.order == 17
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team17"

    # 7.2.4.1.2. Международный принцип
    # Последовательность не стартовавших эстафетных групп
    @pytest.mark.skip(reason="Not implemented in code")
    def test_18_not_started_team(self):
        team = get_team_by_order(18)
        assert team is not None
        assert team.order == 18
        assert team.place == -1
        assert team.get_leg(1).person.name == "P1_Team18"
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
