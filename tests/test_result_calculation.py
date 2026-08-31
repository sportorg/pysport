"""Regression tests for ResultCalculation.get_group_finishes sort ordering."""

from unittest.mock import patch

import pytest

from sportorg.common.otime import OTime
from sportorg.models.memory import (
    Course,
    Group,
    Person,
    Race,
    RaceType,
    RelayTeam,
    ResultManual,
    ResultStatus,
    new_event,
    race,
    set_current_race_index,
)
from sportorg.models.result.result_calculation import (
    RaceCalculationContext,
    ResultCalculation,
)
from sportorg.models.result.result_tools import recalculate_results

BASE_START_MSEC = 10 * 60 * 60 * 1000


def _make_person(name, group, bib):
    person = Person()
    person.name = name
    person.set_bib(bib)
    person.group = group
    person.start_time = OTime(msec=BASE_START_MSEC)
    return person


def _make_result(person, total_msec, status=ResultStatus.OK):
    result = ResultManual()
    result.person = person
    result.bib = person.bib
    result.start_time = OTime(msec=BASE_START_MSEC)
    result.finish_time = OTime(msec=BASE_START_MSEC + total_msec)
    result.status = status
    return result


@pytest.fixture
def time_race():
    """Three athletes with different finish times."""
    new_event([Race()])
    set_current_race_index(0)

    group = Group()
    group.name = "M21"
    race().groups.append(group)

    persons = [
        _make_person("Slow", group, 1),
        _make_person("Fast", group, 2),
        _make_person("Mid", group, 3),
    ]
    results = [
        _make_result(persons[0], 600000),
        _make_result(persons[1], 300000),
        _make_result(persons[2], 480000),
    ]
    race().persons.extend(persons)
    race().results.extend(results)
    return {"group": group, "persons": persons, "results": results}


def test_sort_key_time_mode(time_race):
    """Results sorted by finish time ascending."""
    calc = ResultCalculation(race())
    finishes = calc.get_group_finishes(time_race["group"])

    assert [r.person.name for r in finishes] == ["Fast", "Mid", "Slow"]


def test_sort_key_zero_time_last():
    """A result with zero total time sorts after non-zero results."""
    new_event([Race()])
    set_current_race_index(0)

    group = Group()
    group.name = "W21"
    race().groups.append(group)

    persons = [
        _make_person("Zero", group, 1),
        _make_person("NonZero", group, 2),
    ]
    zero_result = ResultManual()
    zero_result.person = persons[0]
    zero_result.bib = persons[0].bib
    zero_result.start_time = OTime(msec=BASE_START_MSEC)
    zero_result.finish_time = OTime(msec=BASE_START_MSEC)
    zero_result.status = ResultStatus.OK

    nonzero_result = _make_result(persons[1], 300000)

    race().persons.extend(persons)
    race().results.extend([zero_result, nonzero_result])

    calc = ResultCalculation(race())
    finishes = calc.get_group_finishes(group)

    assert [r.person.name for r in finishes] == ["NonZero", "Zero"]


def test_sort_key_status_ordering():
    """Non-OK results sort by status value, then by the usual result order."""
    new_event([Race()])
    set_current_race_index(0)

    group = Group()
    group.name = "M35"
    race().groups.append(group)

    persons = [
        _make_person("OK", group, 1),
        _make_person("DSQ_SLOW", group, 2),
        _make_person("MP", group, 3),
        _make_person("DSQ_FAST", group, 4),
    ]
    ok_result = _make_result(persons[0], 300000, ResultStatus.OK)
    dsq_slow = _make_result(persons[1], 600000, ResultStatus.DISQUALIFIED)
    mp_result = _make_result(persons[2], 400000, ResultStatus.MISSING_PUNCH)
    dsq_fast = _make_result(persons[3], 200000, ResultStatus.DISQUALIFIED)

    race().persons.extend(persons)
    race().results.extend([dsq_slow, mp_result, ok_result, dsq_fast])

    calc = ResultCalculation(race())
    finishes = calc.get_group_finishes(group)

    assert [r.person.name for r in finishes] == ["OK", "DSQ_FAST", "DSQ_SLOW", "MP"]


def test_sort_key_scores_mode():
    """In scores mode, higher rogaine_score wins."""
    new_event([Race()])
    set_current_race_index(0)

    group = Group()
    group.name = "Score"
    race().groups.append(group)
    race().set_setting("result_processing_mode", "scores")

    persons = [
        _make_person("LowScore", group, 1),
        _make_person("HighScore", group, 2),
    ]
    low = _make_result(persons[0], 300000)
    low.rogaine_score = 50
    high = _make_result(persons[1], 400000)
    high.rogaine_score = 100

    race().persons.extend(persons)
    race().results.extend([low, high])

    calc = ResultCalculation(race())
    finishes = calc.get_group_finishes(group)

    assert [r.person.name for r in finishes] == ["HighScore", "LowScore"]


def test_sort_key_ardf_mode():
    """In ARDF mode, higher scores_ardf wins."""
    new_event([Race()])
    set_current_race_index(0)

    group = Group()
    group.name = "ARDF"
    race().groups.append(group)
    race().set_setting("result_processing_mode", "ardf")

    persons = [
        _make_person("LowArdf", group, 1),
        _make_person("HighArdf", group, 2),
    ]
    low = _make_result(persons[0], 300000)
    low.scores_ardf = 30
    high = _make_result(persons[1], 400000)
    high.scores_ardf = 80

    race().persons.extend(persons)
    race().results.extend([low, high])

    calc = ResultCalculation(race())
    finishes = calc.get_group_finishes(group)

    assert [r.person.name for r in finishes] == ["HighArdf", "LowArdf"]


def test_sort_key_shared_context_reuses_cache(time_race):
    """A shared context avoids re-sorting on repeated access."""
    context = RaceCalculationContext(race())
    calc1 = ResultCalculation(race(), context)
    calc2 = ResultCalculation(race(), context)

    finishes1 = calc1.get_group_finishes(time_race["group"])
    finishes2 = calc2.get_group_finishes(time_race["group"])

    assert finishes1 is finishes2
    assert len(finishes1) == 3


def test_context_invalidate_group(time_race):
    """Invalidating a group clears its cached results."""
    context = RaceCalculationContext(race())
    calc = ResultCalculation(race(), context)
    calc.get_group_finishes(time_race["group"])
    assert time_race["group"] in context._group_finishes

    context.invalidate_group(time_race["group"])
    assert time_race["group"] not in context._group_finishes
    assert time_race["group"] not in context._group_persons


def test_partial_recalculation_process_results():
    """process_results(groups=[g]) only recalculates the specified group."""
    new_event([Race()])
    set_current_race_index(0)

    group_a = Group()
    group_a.name = "A"
    group_b = Group()
    group_b.name = "B"
    race().groups.extend([group_a, group_b])

    persons_a = [_make_person("A1", group_a, 1)]
    persons_b = [_make_person("B1", group_b, 2)]
    results = [
        _make_result(persons_a[0], 300000),
        _make_result(persons_b[0], 400000),
    ]
    race().persons.extend(persons_a + persons_b)
    race().results.extend(results)

    context = RaceCalculationContext(race())
    calc = ResultCalculation(race(), context)
    calc.process_results(groups=[group_a])

    assert results[0].place == 1
    assert results[1].place == 0


def test_partial_recalculation_updates_previous_and_new_groups():
    """A cross-group result assignment refreshes places in both groups."""
    new_event([Race()])
    set_current_race_index(0)

    group_a = Group()
    group_a.name = "A"
    group_b = Group()
    group_b.name = "B"
    race().groups.extend([group_a, group_b])

    persons_a = [
        _make_person("Moved", group_a, 1),
        _make_person("Remaining", group_a, 2),
    ]
    person_b = _make_person("B1", group_b, 3)
    moved = _make_result(persons_a[0], 300000)
    remaining = _make_result(persons_a[1], 600000)
    other = _make_result(person_b, 400000)
    race().persons.extend(persons_a + [person_b])
    race().results.extend([moved, remaining, other])
    recalculate_results(recheck_results=False)

    assert moved.place == 1
    assert remaining.place == 2
    assert other.place == 1

    moved.person.group = group_b
    recalculate_results(recheck_results=False, groups=[group_a, group_b])

    assert moved.place == 1
    assert remaining.place == 1
    assert other.place == 2


def test_partial_recalculation_preserves_other_relay_groups():
    """Partial processing replaces relay teams only for affected groups."""
    new_event([Race()])
    set_current_race_index(0)

    group_a = Group()
    group_a.name = "A"
    group_b = Group()
    group_b.name = "B"
    group_b.set_type(RaceType.RELAY)
    race().groups.extend([group_a, group_b])

    relay_team = RelayTeam(race())
    relay_team.group = group_b
    relay_team.bib_number = 7
    race().relay_teams.append(relay_team)

    person = _make_person("A1", group_a, 1)
    result = _make_result(person, 300000)
    race().persons.append(person)
    race().results.append(result)

    recalculate_results(recheck_results=False, group=group_a)

    assert race().relay_teams == [relay_team]
    assert result.place == 1


def test_partial_recalculation_rechecks_affected_groups():
    """The default recheck flag is honored for group-only recalculation."""
    new_event([Race()])
    set_current_race_index(0)

    group = Group()
    group.name = "A"
    race().groups.append(group)
    person = _make_person("A1", group, 1)
    result = _make_result(person, 300000)
    race().persons.append(person)
    race().results.append(result)

    with patch(
        "sportorg.models.result.result_tools.ResultChecker.checking"
    ) as checking:
        recalculate_results(group=group)

    assert checking.call_count == 1
    checking.assert_called_once_with(result)
