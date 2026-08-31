"""Regression tests freezing current split calculation behavior.

Covers PersonSplits generation, GroupSplits ranking (competition ranking
1, 1, 3), stable tie ordering, missing punches, courses without controls,
leader tracking, and final individual/relay ordering.
"""

import pytest

from sportorg.common.otime import OTime
from sportorg.models.memory import (
    Course,
    CourseControl,
    Group,
    Person,
    Race,
    RaceType,
    ResultManual,
    Split,
    new_event,
    race,
    set_current_race_index,
)
from sportorg.models.result.split_calculation import GroupSplits, PersonSplits

BASE_START_MSEC = 10 * 60 * 60 * 1000  # 10:00:00.000


def make_otime(msec: int) -> OTime:
    return OTime(msec=msec)


def make_course(code_prefix: str, leg_count: int) -> Course:
    course = Course()
    for i in range(leg_count):
        control = CourseControl()
        control.code = "{}0{}".format(code_prefix, i + 1)
        control.length = 1000
        course.controls.append(control)
    return course


def make_person(name: str, group: Group, bib: int) -> Person:
    person = Person()
    person.name = name
    person.set_bib(bib)
    person.group = group
    # ResultSportident resolves the start from person.start_time ("protocol" source)
    person.start_time = make_otime(BASE_START_MSEC)
    return person


def make_result(
    person: Person,
    leg_times_msec,
    start_msec: int = BASE_START_MSEC,
    incorrect_punch_msec=None,
) -> ResultManual:
    """Build a result with cumulative splits; one optional incorrect punch."""
    result = ResultManual()
    result.person = person
    result.bib = person.bib
    result.start_time = make_otime(start_msec)
    cursor = start_msec
    for leg_msec in leg_times_msec:
        if (
            incorrect_punch_msec is not None
            and cursor < incorrect_punch_msec <= cursor + leg_msec
        ):
            wrong = Split()
            wrong.time = make_otime(incorrect_punch_msec)
            wrong.is_correct = False
            result.splits.append(wrong)
        cursor += leg_msec
        split = Split()
        split.time = make_otime(cursor)
        result.splits.append(split)
    result.finish_time = make_otime(cursor)
    return result


@pytest.fixture
def individual_race():
    """Three athletes, 2-control course.

    Alice: legs 5:00 / 5:00 (total 10:00) — wins leg 1, ties leg 2.
    Bob:   legs 6:00 / 4:00 (total 10:00) — second on leg 1, ties leg 2.
    Carol: legs 7:00 / 3:00 (total 10:00) — third on leg 1, ties leg 2.
    """
    new_event([Race()])
    set_current_race_index(0)

    course = make_course("1", 2)
    group = Group()
    group.name = "M21"
    group.course = course

    alice = make_person("Alice", group, 1)
    bob = make_person("Bob", group, 2)
    carol = make_person("Carol", group, 3)

    results = [
        make_result(alice, [300000, 300000]),
        make_result(bob, [360000, 240000]),
        make_result(carol, [420000, 180000]),
    ]

    race().courses.append(course)
    race().groups.append(group)
    race().persons.extend([alice, bob, carol])
    race().results.extend(results)
    return {"course": course, "group": group, "results": results}


def test_person_splits_leg_and_relative_times(individual_race):
    person_splits = PersonSplits(race(), individual_race["results"][0]).generate()

    first = person_splits.get_leg_by_course_index(0)
    second = person_splits.get_leg_by_course_index(1)

    assert first.leg_time == make_otime(300000)
    assert second.leg_time == make_otime(300000)
    assert first.relative_time == make_otime(300000)
    assert second.relative_time == make_otime(600000)
    assert person_splits.get_leg_by_course_index(2) is None
    assert person_splits.get_last_correct_index() == 1


def test_set_places_ranking_ties_and_leader(individual_race):
    group_splits = GroupSplits(race(), individual_race["group"]).generate()

    results = individual_race["results"]
    # leg 1: 5:00 < 6:00 < 7:00 -> places 1, 2, 3
    assert results[0].splits[0].leg_place == 1
    assert results[1].splits[0].leg_place == 2
    assert results[2].splits[0].leg_place == 3
    # leg 2: 5:00, 4:00, 3:00 -> places 3, 2, 1
    assert results[0].splits[1].leg_place == 3
    assert results[1].splits[1].leg_place == 2
    assert results[2].splits[1].leg_place == 1
    # relative (cumulative) times all equal 10:00 -> competition ranking 1, 1, 1
    for result in results:
        assert result.splits[1].relative_time == make_otime(600000)
        assert result.splits[1].relative_place == 1

    # leader_time is set only for leg ranking
    assert results[0].splits[0].leader_time == make_otime(300000)
    assert results[2].splits[1].leader_time == make_otime(180000)

    assert group_splits.get_leg_leader(0) == ("Alice", make_otime(300000))
    assert group_splits.get_leg_leader(1) == ("Carol", make_otime(180000))
    assert group_splits.get_leg_leader(2) == ("", "")


def test_equal_leg_times_competition_ranking():
    """Equal leg times produce competition ranking 1, 1, 3."""
    new_event([Race()])
    set_current_race_index(0)

    course = make_course("2", 1)
    group = Group()
    group.name = "W21"
    group.course = course

    persons = [
        make_person("First", group, 11),
        make_person("Second", group, 12),
        make_person("Third", group, 13),
    ]
    results = [
        make_result(persons[0], [300000]),
        make_result(persons[1], [300000]),
        make_result(persons[2], [360000]),
    ]

    race().courses.append(course)
    race().groups.append(group)
    race().persons.extend(persons)
    race().results.extend(results)

    group_splits = GroupSplits(race(), group).generate()

    assert results[0].splits[0].leg_place == 1
    assert results[1].splits[0].leg_place == 1
    assert results[2].splits[0].leg_place == 3
    # stable tie ordering: race order is preserved, first person wins the tie
    assert group_splits.get_leg_leader(0) == ("First", make_otime(300000))
    assert [ps.person.name for ps in group_splits.person_splits] == [
        "First",
        "Second",
        "Third",
    ]


def test_missing_punch_gets_no_place():
    """A person without a split for a leg gets no place; leader stays correct."""
    new_event([Race()])
    set_current_race_index(0)

    course = make_course("3", 2)
    group = Group()
    group.name = "M35"
    group.course = course

    complete = make_person("Complete", group, 21)
    missing = make_person("Missing", group, 22)

    complete_result = make_result(complete, [300000, 300000])
    missing_result = make_result(missing, [300000])  # only one of two controls

    race().courses.append(course)
    race().groups.append(group)
    race().persons.extend([complete, missing])
    race().results.extend([complete_result, missing_result])

    group_splits = GroupSplits(race(), group).generate()

    # leg 0: equal leg times tie at place 1 (competition ranking)
    assert complete_result.splits[0].leg_place == 1
    assert missing_result.splits[0].leg_place == 1
    # leg 1: only Complete has a leg
    assert complete_result.splits[1].leg_place == 1
    assert len(missing_result.splits) == 1
    assert group_splits.get_leg_leader(1) == ("Complete", make_otime(300000))


def test_extra_incorrect_punch_is_skipped():
    new_event([Race()])
    set_current_race_index(0)

    course = make_course("4", 2)
    group = Group()
    group.name = "W35"
    group.course = course

    person = make_person("Extra", group, 31)
    # incorrect punch 1 minute into the first leg
    result = make_result(
        person, [300000, 300000], incorrect_punch_msec=BASE_START_MSEC + 60000
    )

    race().courses.append(course)
    race().groups.append(group)
    race().persons.append(person)
    race().results.append(result)

    PersonSplits(race(), result).generate()

    assert len(result.splits) == 3
    wrong, first, second = result.splits
    assert wrong.is_correct is False
    assert wrong.course_index == -1
    assert first.course_index == 0
    assert second.course_index == 1
    # leg time is measured from leg start, ignoring the wrong punch
    assert first.leg_time == make_otime(300000)
    assert second.leg_time == make_otime(300000)


def test_course_without_controls_assigns_sequential_indexes():
    new_event([Race()])
    set_current_race_index(0)

    course = Course()  # no controls
    group = Group()
    group.name = "Open"
    group.course = course

    person = make_person("Solo", group, 41)
    result = make_result(person, [120000, 180000])

    race().courses.append(course)
    race().groups.append(group)
    race().persons.append(person)
    race().results.append(result)

    person_splits = PersonSplits(race(), result).generate()

    assert result.splits[0].course_index == 0
    assert result.splits[1].course_index == 1
    assert result.splits[0].leg_time == make_otime(120000)
    assert result.splits[1].leg_time == make_otime(180000)
    # frozen quirk: course_index is assigned without a course, but
    # last_correct_index only advances in the course-matching loop
    assert person_splits.get_last_correct_index() == -1
    # group has no controls -> no ranking is performed
    group_splits = GroupSplits(race(), group).generate()
    assert group_splits.cp_count == 0
    assert result.splits[0].leg_place == 0


def test_final_ordering_individual_by_result(individual_race):
    """Frozen quirk: all totals are equal, and the leg-2 relative sort before
    sort_by_result leaves the reversed leg-2 ranking (Carol, Bob, Alice);
    the stable result sort then preserves that order."""
    group_splits = GroupSplits(race(), individual_race["group"]).generate()

    assert [ps.person.name for ps in group_splits.person_splits] == [
        "Carol",
        "Bob",
        "Alice",
    ]


def test_final_ordering_relay_by_place():
    new_event([Race()])
    set_current_race_index(0)

    course = make_course("5", 1)
    group = Group()
    group.name = "Relay"
    group.course = course
    group.set_type(RaceType.RELAY)

    # team 1 legs 1-2, team 2 legs 1-2; team 2 is faster on both legs
    persons = [
        make_person("T1L1", group, 1001),
        make_person("T1L2", group, 2001),
        make_person("T2L1", group, 1002),
        make_person("T2L2", group, 2002),
    ]
    results = [
        make_result(persons[0], [300000]),
        make_result(persons[1], [300000]),
        make_result(persons[2], [240000]),
        make_result(persons[3], [240000]),
    ]
    # cumulative relay result must grow per leg so result sorting is stable
    results[1].finish_time = make_otime(BASE_START_MSEC + 600000)
    results[3].finish_time = make_otime(BASE_START_MSEC + 480000)
    for result, place in zip(results, [2, 2, 1, 1]):
        result.place = place

    race().courses.append(course)
    race().groups.append(group)
    race().persons.extend(persons)
    race().results.extend(results)

    group_splits = GroupSplits(race(), group).generate()

    # sort_by_place: place first, then relay leg number
    assert [ps.person.name for ps in group_splits.person_splits] == [
        "T2L1",
        "T2L2",
        "T1L1",
        "T1L2",
    ]
