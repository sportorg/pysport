"""Benchmarks for split calculation ranking.

Measures GroupSplits.set_places() on a deterministic 500 person x 50 control
dataset and RaceSplits.generate() on a multi-group race. Timings are recorded
in the plan Action Log; no wall-clock thresholds are asserted here.
"""

import pytest

from sportorg.common.otime import OTime
from sportorg.models.memory import (
    Course,
    CourseControl,
    Group,
    Person,
    Race,
    ResultManual,
    Split,
    new_event,
    race,
    set_current_race_index,
)
from sportorg.models.result.split_calculation import (
    GroupSplits,
    PersonSplits,
    RaceSplits,
)

PERSON_COUNT = 500
CONTROL_COUNT = 50
GROUP_COUNT = 20
GROUP_SIZE = 25
BASE_START_MSEC = 10 * 60 * 60 * 1000  # 10:00:00.000


def _make_course(control_count: int) -> Course:
    course = Course()
    for index in range(control_count):
        control = CourseControl()
        control.code = str(101 + index)
        control.length = 1000
        course.controls.append(control)
    return course


def _make_result(person: Person, leg_count: int, seed: int) -> ResultManual:
    result = ResultManual()
    result.person = person
    result.bib = person.bib
    result.start_time = OTime(msec=BASE_START_MSEC)
    cursor = BASE_START_MSEC
    for index in range(leg_count):
        # deterministic pseudo-random leg times between 3:00 and 8:59
        leg_msec = 180000 + ((seed * 7919 + index * 104729) % 3600) * 100
        cursor += leg_msec
        split = Split()
        split.time = OTime(msec=cursor)
        result.splits.append(split)
    result.finish_time = OTime(msec=cursor)
    return result


def _build_group(bib_offset: int, control_count: int, size: int) -> Group:
    course = _make_course(control_count)
    group = Group()
    group.name = "G{}".format(bib_offset)
    group.course = course

    race().courses.append(course)
    race().groups.append(group)
    for index in range(size):
        person = Person()
        person.name = "P{}".format(bib_offset + index)
        person.set_bib(bib_offset + index)
        person.start_time = OTime(msec=BASE_START_MSEC)
        person.group = group
        race().persons.append(person)
        race().results.append(_make_result(person, control_count, bib_offset + index))
    return group


def _reset_places(group_splits: GroupSplits) -> None:
    for person_split in group_splits.person_splits:
        for split in person_split.result.splits:
            split.leg_place = 0
            split.relative_place = 0
            split.leader_time = OTime()
    group_splits.leader = {}


@pytest.fixture
def large_group_splits():
    new_event([Race()])
    set_current_race_index(0)
    group = _build_group(1000, CONTROL_COUNT, PERSON_COUNT)

    group_splits = GroupSplits(race(), group)
    for result in race().results:
        group_splits.person_splits.append(PersonSplits(race(), result).generate())
    return group_splits


@pytest.fixture
def multi_group_race():
    new_event([Race()])
    set_current_race_index(0)
    for group_index in range(GROUP_COUNT):
        _build_group(1000 * (group_index + 1), 10, GROUP_SIZE)
    return race()


def test_set_places_500x50(benchmark, large_group_splits):
    def run():
        _reset_places(large_group_splits)
        large_group_splits.set_places()

    benchmark(run)
    assert len(large_group_splits.person_splits) == PERSON_COUNT


def test_multi_group_generation(benchmark, multi_group_race):
    benchmark(RaceSplits(multi_group_race).generate)
    assert len(multi_group_race.groups) == GROUP_COUNT
