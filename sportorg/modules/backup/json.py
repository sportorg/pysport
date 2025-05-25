import gzip
import os
import uuid

import orjson

from sportorg import config
from sportorg.models.memory import (
    Race,
    get_current_race_index,
    new_event,
    race,
    races,
    set_current_race_index,
)
from sportorg.models.result.result_tools import recalculate_results


def dump(file, *, compress=False):
    data = {
        "version": config.VERSION,
        "current_race": get_current_race_index(),
        "races": [r.to_dict() for r in races()],
    }
    raw = orjson.dumps(data, option=orjson.OPT_INDENT_2)
    if compress:
        file.write(gzip.compress(raw))
    else:
        file.write(raw.decode())
    file.flush()
    os.fsync(file.fileno())


def load(file, *, compress=False):
    # clear current race, here we'll have index data after loading
    tmp_obj = Race()
    new_event([tmp_obj])

    event, current_race = get_races_from_file(file, compress=compress)
    new_event(event)
    set_current_race_index(current_race)

    obj = race()
    recalculate_results(race_object=obj)

    obj.set_setting(
        "live_enabled", False
    )  # force user to activate Live broadcast manually (not to lose live results)


def get_races_from_file(file, *, compress=False):
    if compress:
        data = orjson.loads(gzip.decompress(file.read()))
    else:
        data = orjson.loads(file.read())
    if "races" not in data:
        data = {
            "races": [data] if not isinstance(data, list) else data,
            "current_race": 0,
        }
    event = []
    for race_dict in data["races"]:
        _race_migrate(race_dict)
        obj = Race()
        obj.id = uuid.UUID(str(race_dict["id"]))
        obj.update_data(race_dict)
        # while parsing of data index is created in old object, available as race()
        _move_indexes_to_new_race(obj)
        event.append(obj)
    current_race = 0
    if "current_race" in data:
        current_race = int(data["current_race"])
    return event, current_race


def _move_indexes_to_new_race(obj):
    obj.person_index_bib = race().person_index_bib
    race().person_index_bib = {}
    obj.person_index_card = race().person_index_card
    race().person_index_card = {}
    obj.course_index_name = race().course_index_name
    race().course_index_name = {}


def _race_migrate(data):
    for person in data["persons"]:
        if "sportident_card" in person:
            person["card_number"] = person["sportident_card"]
        if "is_rented_sportident_card" in person:
            person["is_rented_card"] = person["is_rented_sportident_card"]
    for result in data["results"]:
        if "sportident_card" in result:
            result["card_number"] = result["sportident_card"]
    for group in data["groups"]:
        if "min_year" not in group:
            group["min_year"] = 0
        if "max_year" not in group:
            group["max_year"] = 0
    for org in data["organizations"]:
        if "address" in org and org["address"]:
            org["country"] = org["address"]["country"]["name"]
            org["region"] = org["address"]["state"]
            if org["contact"]:
                org["contact"] = org["contact"]["value"]
    settings = data["settings"]
    if "sportident_zero_time" in settings:
        settings["system_zero_time"] = settings["sportident_zero_time"]
    if "sportident_start_source" in settings:
        settings["system_start_source"] = settings["sportident_start_source"]
    if "sportident_start_cp_number" in settings:
        settings["system_start_cp_number"] = settings["sportident_start_cp_number"]
    if "sportident_finish_source" in settings:
        settings["system_finish_source"] = settings["sportident_finish_source"]
    if "sportident_finish_cp_number" in settings:
        settings["system_finish_cp_number"] = settings["sportident_finish_cp_number"]
    if "sportident_assign_chip_reading" in settings:
        settings["system_assign_chip_reading"] = settings[
            "sportident_assign_chip_reading"
        ]
    if "sportident_assignment_mode" in settings:
        settings["system_assignment_mode"] = settings["sportident_assignment_mode"]
    if "sportident_port" in settings:
        settings["system_port"] = settings["sportident_port"]
    return data
