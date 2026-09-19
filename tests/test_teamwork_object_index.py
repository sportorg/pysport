"""Reproduction of teamwork sync defects caused by a stale/incomplete object index.

Teamwork transports objects as `obj.to_dict()` and applies them with
`Race.update_data(dict)`.  `update_data` decides between *update* and *create*
purely by `Race.get_obj(name, id)`, which is a lookup in `Race.index_obj`
(person_index / result_index / group_index / course_index / organization_index).

Every defect below is a consequence of that index not matching `Race.persons`,
`Race.results`, `Race.groups`, `Race.courses`, `Race.organizations`.
"""

import uuid

import pytest

from sportorg.models.memory import (
    Course,
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
def sender() -> Race:
    """A race holding one person + one manual result, both properly indexed."""
    new_event([Race()])
    set_current_race_index(0)
    obj = race()

    group = Group()
    group.name = "M21"
    obj.groups.append(group)
    obj.group_index[str(group.id)] = group

    org = Organization()
    org.name = "Org1"
    obj.organizations.append(org)
    obj.organization_index[str(org.id)] = org

    person = Person()
    person.name = "Ivan"
    person.surname = "Ivanov"
    person.group = group
    person.organization = org
    obj.persons.append(person)
    obj.person_index[str(person.id)] = person

    result = ResultManual()
    result.person = person
    obj.results.append(result)
    obj.result_index[str(result.id)] = result

    return obj


def receiver_from(sender: Race) -> Race:
    """Second copy of the program: same race loaded from the same file."""
    obj = Race()
    obj.id = sender.id
    obj.update_data(sender.to_dict())
    return obj


# --------------------------------------------------------------------------
# Bug 1: object received over teamwork is duplicated under the same id
# --------------------------------------------------------------------------


def test_result_added_by_gui_is_not_duplicated_on_receive(sender: Race) -> None:
    """result_edit.py does `race().results.insert(0, result)` without indexing."""
    receiver = receiver_from(sender)

    result = ResultManual()
    receiver.results.insert(0, result)  # exactly what ResultEditDialog does
    sender.results.append(result)
    sender.result_index[str(result.id)] = result

    receiver.update_data(result.to_dict())

    ids = [str(r.id) for r in receiver.results]
    assert len(ids) == len(set(ids)), f"duplicate result ids: {ids}"


def test_person_added_by_gui_is_not_duplicated_on_receive(sender: Race) -> None:
    """`Race.add_person` indexes bib/card but never `person_index`."""
    receiver = receiver_from(sender)

    person = Person()
    person.name = "Petr"
    receiver.add_person(person)  # GUI "add person" path
    sender.persons.append(person)
    sender.person_index[str(person.id)] = person

    receiver.update_data(person.to_dict())

    ids = [str(p.id) for p in receiver.persons]
    assert len(ids) == len(set(ids)), f"duplicate person ids: {ids}"


def test_duplicated_result_delete_removes_only_one(sender: Race) -> None:
    """Two results sharing an id: deleting one wipes both (delete_*_by_id)."""
    receiver = receiver_from(sender)
    result = receiver.results[0]

    clone = ResultManual()
    clone.id = result.id  # what create_obj produces on a duplicate receive
    receiver.results.append(clone)

    receiver.delete_results_by_id([result.id])

    assert len(receiver.results) == 1


# --------------------------------------------------------------------------
# Bug 2: deleted object cannot be restored by re-sending it
# --------------------------------------------------------------------------


def test_deleted_person_is_restored_on_receive(sender: Race) -> None:
    receiver = receiver_from(sender)
    person_dict = receiver.persons[0].to_dict()

    receiver.delete_persons_by_id([receiver.persons[0].id])
    assert receiver.persons == []

    receiver.update_data(person_dict)

    assert len(receiver.persons) == 1


def test_deleted_result_is_restored_on_receive(sender: Race) -> None:
    receiver = receiver_from(sender)
    result_dict = receiver.results[0].to_dict()

    receiver.delete_results_by_id([receiver.results[0].id])
    assert receiver.results == []

    receiver.update_data(result_dict)

    assert len(receiver.results) == 1


def test_deleted_group_is_restored_on_receive(sender: Race) -> None:
    receiver = receiver_from(sender)
    group_dict = receiver.groups[0].to_dict()

    receiver.delete_persons_by_id([p.id for p in receiver.persons])
    receiver.delete_groups_by_id([receiver.groups[0].id])
    assert receiver.groups == []

    receiver.update_data(group_dict)

    assert len(receiver.groups) == 1


def test_deleted_organization_is_restored_on_receive(sender: Race) -> None:
    receiver = receiver_from(sender)
    org_dict = receiver.organizations[0].to_dict()

    receiver.delete_persons_by_id([p.id for p in receiver.persons])
    receiver.delete_organizations_by_id([receiver.organizations[0].id])
    assert receiver.organizations == []

    receiver.update_data(org_dict)

    assert len(receiver.organizations) == 1


def test_deleted_course_is_restored_on_receive(sender: Race) -> None:
    receiver = receiver_from(sender)
    course = Course()
    course.name = "C1"
    receiver.courses.append(course)
    receiver.course_index[str(course.id)] = course
    course_dict = course.to_dict()

    receiver.delete_courses_by_id([course.id])
    assert receiver.courses == []

    receiver.update_data(course_dict)

    assert len(receiver.courses) == 1


# --------------------------------------------------------------------------
# The shared root cause: index keys are str(uuid), removal code uses uuid.UUID
# --------------------------------------------------------------------------


def test_delete_by_index_drops_index_entry(sender: Race) -> None:
    person = sender.persons[0]
    sender.delete_persons([0])
    assert sender.get_obj("Person", str(person.id)) is None


def test_delete_results_by_index_drops_index_entry(sender: Race) -> None:
    result = sender.results[0]
    sender.delete_results([0])
    assert sender.get_obj("ResultManual", str(result.id)) is None


def test_lookup_never_returns_a_detached_object(sender: Race) -> None:
    """After any delete, get_obj must not resolve the removed ids any more."""
    receiver = receiver_from(sender)
    result_ids = [str(r.id) for r in receiver.results]
    person_ids = [str(p.id) for p in receiver.persons]

    receiver.delete_results_by_id([r.id for r in receiver.results])
    receiver.delete_persons_by_id([p.id for p in receiver.persons])

    for result_id in result_ids:
        assert receiver.get_obj("ResultManual", result_id) is None
    for person_id in person_ids:
        assert receiver.get_obj("Person", person_id) is None


def test_lookup_finds_every_object_of_the_race(sender: Race) -> None:
    """Objects appended directly to the race lists must still be found by id."""
    receiver = receiver_from(sender)
    person = Person()
    receiver.persons.append(person)
    result = ResultManual()
    receiver.results.append(result)

    assert receiver.get_obj("Person", str(person.id)) is person
    assert receiver.get_obj("ResultManual", str(result.id)) is result


def test_lookup_survives_whole_list_replacement(sender: Race) -> None:
    """Table sorting assigns a plain list back to the race."""
    receiver = receiver_from(sender)
    person = Person()
    receiver.persons = list(receiver.persons) + [person]

    assert receiver.get_obj("Person", str(person.id)) is person


# --------------------------------------------------------------------------
# Table filtering pops rows out of the race lists without deleting them
# --------------------------------------------------------------------------


def test_filtered_out_person_is_updated_not_duplicated(sender: Race) -> None:
    """AbstractSportOrgMemoryModel.apply_filter moves rows to filter_backup."""
    receiver = receiver_from(sender)
    person = receiver.persons[0]
    person_dict = person.to_dict()
    assert receiver.get_obj("Person", str(person.id)) is person  # table shown once

    filter_backup = [receiver.persons.pop(0)]  # what apply_filter does

    person_dict["name"] = "Updated"
    receiver.update_data(person_dict)

    receiver.persons.extend(filter_backup)  # what clear_filter does

    assert len(receiver.persons) == 1
    assert receiver.persons[0].name == "Updated"


def test_filtered_out_result_is_updated_not_duplicated(sender: Race) -> None:
    receiver = receiver_from(sender)
    result = receiver.results[0]
    result_dict = result.to_dict()
    assert receiver.get_obj("ResultManual", str(result.id)) is result

    filter_backup = [receiver.results.pop(0)]

    result_dict["bib"] = 42
    receiver.update_data(result_dict)

    receiver.results.extend(filter_backup)

    assert len(receiver.results) == 1
    assert receiver.results[0].bib == 42
