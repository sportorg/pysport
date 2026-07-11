from typing import List

import pytest

from sportorg.models.memory import (
    Course,
    CourseControl,
    Group,
    Organization,
    Person,
    Race,
    ResultManual,
    new_event,
    race,
    set_current_race_index,
)


@pytest.fixture
def r() -> Race:
    """Race with 2 courses, 3 groups, 2 orgs, 4 persons, 4 results.

    Layout:
      courses:  [C1, C2]
      groups:   [M21→C1, W21→C2, M35→no course]
      orgs:     [Org1, Org2]
      persons:  [p0(M21/Org1), p1(M21/Org1), p2(W21/Org2), p3(M35/Org1)]
      results:  [res0..res3] mapped 1-to-1 to persons in same order
    """
    new_event([Race()])
    set_current_race_index(0)
    obj = race()

    c1, c2 = Course(), Course()
    c1.name, c2.name = "C1", "C2"
    # Add a control to c2 to make it distinct from c1 (since Course.__eq__ checks controls)
    c2_control = CourseControl()
    c2_control.code = "31"
    c2.controls.append(c2_control)
    obj.courses.extend([c1, c2])

    g1, g2, g3 = Group(), Group(), Group()
    g1.name, g2.name, g3.name = "M21", "W21", "M35"
    g1.course, g2.course = c1, c2  # g3 intentionally has no course
    obj.groups.extend([g1, g2, g3])

    o1, o2 = Organization(), Organization()
    o1.name, o2.name = "Org1", "Org2"
    obj.organizations.extend([o1, o2])

    p0, p1, p2, p3 = Person(), Person(), Person(), Person()
    p0.group, p0.organization = g1, o1
    p1.group, p1.organization = g1, o1
    p2.group, p2.organization = g2, o2
    p3.group, p3.organization = g3, o1
    obj.persons.extend([p0, p1, p2, p3])

    for p in obj.persons:
        res = ResultManual()
        res.person = p
        obj.results.append(res)

    return obj


# --- _build_partial ---


def test_build_partial_empty_returns_none(r: Race) -> None:
    assert r._build_partial([]) is None


def test_build_partial_groups_in_model_order(r: Race) -> None:
    # Supply persons from W21 (index 1) then M21 (index 0) — reversed group order
    persons_W21 = [p for p in r.persons if p.group and p.group.name == "W21"]
    persons_m21 = [p for p in r.persons if p.group and p.group.name == "M21"]
    result = r._build_partial(persons_W21 + persons_m21)
    assert result is not None
    group_names = [g["name"] for g in result["groups"]]
    assert group_names == ["M21", "W21"]  # self.groups order, not input order


def test_build_partial_courses_in_model_order(r: Race) -> None:
    # M21→C1 (index 0), W21→C2 (index 1); supply W21 persons first
    persons_W21 = [p for p in r.persons if p.group and p.group.name == "W21"]
    persons_m21 = [p for p in r.persons if p.group and p.group.name == "M21"]
    result = r._build_partial(persons_W21 + persons_m21)
    assert result is not None
    course_names = [c["name"] for c in result["courses"]]
    assert course_names == ["C1", "C2"]  # self.courses order


def test_build_partial_orgs_in_model_order(r: Race) -> None:
    # p2 is in Org2 (index 1), p0 is in Org1 (index 0); supply p2 first
    p0, p2 = r.persons[0], r.persons[2]
    result = r._build_partial([p2, p0])
    assert result is not None
    org_names = [o["name"] for o in result["organizations"]]
    assert org_names == ["Org1", "Org2"]  # self.organizations order


def test_build_partial_results_filtered(r: Race) -> None:
    # Only p0 and p1 (M21) — results must be exactly theirs, in self.results order
    persons_m21 = [p for p in r.persons if p.group and p.group.name == "M21"]
    result = r._build_partial(persons_m21)
    assert result is not None
    actual_person_ids = [res["person_id"] for res in result["results"]]
    expected_person_ids = [
        str(res.person.id) for res in r.results if res.person in persons_m21
    ]
    assert actual_person_ids == expected_person_ids


def test_build_partial_excludes_other_groups(r: Race) -> None:
    persons_m21 = [p for p in r.persons if p.group and p.group.name == "M21"]
    result = r._build_partial(persons_m21)
    assert result is not None
    group_names = [g["name"] for g in result["groups"]]
    assert "W21" not in group_names
    assert "M35" not in group_names


def test_build_partial_group_without_course_excluded_from_courses(r: Race) -> None:
    # M35 has no course → courses list must be empty for M35-only persons
    persons_M35 = [p for p in r.persons if p.group and p.group.name == "M35"]
    result = r._build_partial(persons_M35)
    assert result is not None
    assert result["courses"] == []


def test_build_partial_courses_matched_by_id_not_structure(r: Race) -> None:
    # A decoy course with the same (empty) controls as C1 is structurally equal
    # to it (Course.__eq__ compares controls), but is a different object that no
    # group references. It must be excluded from the result.
    decoy = Course()
    decoy.name = "C1-decoy"
    r.courses.append(decoy)
    persons_m21 = [p for p in r.persons if p.group and p.group.name == "M21"]
    result = r._build_partial(persons_m21)
    assert result is not None
    course_names = [c["name"] for c in result["courses"]]
    assert course_names == ["C1"]


# --- partial_for_persons ---


def test_partial_for_persons_empty_returns_none(r: Race) -> None:
    assert r.partial_for_persons([]) is None


def test_partial_for_persons_reorders_by_model(r: Race) -> None:
    # Reverse the persons list — output must follow self.persons order
    reversed_persons = list(reversed(r.persons))
    result = r.partial_for_persons(reversed_persons)
    assert result is not None
    expected = [str(p.id) for p in r.persons]
    actual = [p["id"] for p in result["persons"]]
    assert actual == expected


def test_partial_for_persons_subset(r: Race) -> None:
    # Supply only p0 and p2 — output persons must be exactly those two
    selected = [r.persons[0], r.persons[2]]
    result = r.partial_for_persons(selected)
    assert result is not None
    assert len(result["persons"]) == 2


# --- partial_for_groups ---


def test_partial_for_groups_empty_returns_none(r: Race) -> None:
    assert r.partial_for_groups([]) is None


def test_partial_for_groups_filters_persons(r: Race) -> None:
    g_m21 = r.groups[0]  # M21 — has p0, p1
    result = r.partial_for_groups([g_m21])
    assert result is not None
    assert len(result["persons"]) == 2
    assert len(result["groups"]) == 1
    assert result["groups"][0]["name"] == "M21"


def test_partial_for_groups_order_follows_model(r: Race) -> None:
    # Select M35 (index 2) and M21 (index 0) in that order
    g_M35, g_m21 = r.groups[2], r.groups[0]
    result = r.partial_for_groups([g_M35, g_m21])
    assert result is not None
    group_names = [g["name"] for g in result["groups"]]
    assert group_names == ["M21", "M35"]  # self.groups order


def test_partial_for_groups_excludes_other_persons(r: Race) -> None:
    g_m21 = r.groups[0]
    result = r.partial_for_groups([g_m21])
    assert result is not None
    person_ids = {p["id"] for p in result["persons"]}
    expected_ids = {str(p.id) for p in r.persons if p.group == g_m21}
    assert person_ids == expected_ids


# --- partial_for_courses ---


def test_partial_for_courses_empty_returns_none(r: Race) -> None:
    assert r.partial_for_courses([]) is None


def test_partial_for_courses_filters_by_course(r: Race) -> None:
    # C1 → M21 only
    result = r.partial_for_courses([r.courses[0]])
    assert result is not None
    group_names = [g["name"] for g in result["groups"]]
    assert group_names == ["M21"]


def test_partial_for_courses_multi(r: Race) -> None:
    # Both courses → M21 and W21 (M35 has no course, excluded)
    result = r.partial_for_courses(r.courses)
    assert result is not None
    group_names = [g["name"] for g in result["groups"]]
    assert "M21" in group_names
    assert "W21" in group_names
    assert "M35" not in group_names


def test_partial_for_courses_matches_by_id_not_structure(r: Race) -> None:
    # Structurally identical to C1 (both have empty controls) but a different
    # object that no group actually references — must not match C1.
    decoy = Course()
    decoy.name = "C1-decoy"
    result = r.partial_for_courses([decoy])
    assert result is None


# --- partial_for_orgs ---


def test_partial_for_orgs_empty_returns_none(r: Race) -> None:
    assert r.partial_for_orgs([]) is None


def test_partial_for_orgs_filters_persons(r: Race) -> None:
    o2 = r.organizations[1]  # Org2 — only p2
    result = r.partial_for_orgs([o2])
    assert result is not None
    assert len(result["persons"]) == 1


def test_partial_for_orgs_multi(r: Race) -> None:
    # Both orgs → all 4 persons, in self.persons order
    result = r.partial_for_orgs(r.organizations)
    assert result is not None
    actual_ids = [p["id"] for p in result["persons"]]
    expected_ids = [str(p.id) for p in r.persons]
    assert actual_ids == expected_ids


# --- partial_for_results ---


def test_partial_for_results_empty_returns_none(r: Race) -> None:
    assert r.partial_for_results([]) is None


def test_partial_for_results_persons_in_model_order(r: Race) -> None:
    # Results in reversed order — output persons must follow self.persons order
    reversed_results = list(reversed(r.results))
    result = r.partial_for_results(reversed_results)
    assert result is not None
    expected = [str(p.id) for p in r.persons]
    actual = [p["id"] for p in result["persons"]]
    assert actual == expected


def test_partial_for_results_subset(r: Race) -> None:
    # Pass only first result — output has exactly 1 person
    result = r.partial_for_results([r.results[0]])
    assert result is not None
    assert len(result["persons"]) == 1
