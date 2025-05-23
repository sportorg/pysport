import logging
from re import subn
from typing import Any, Dict

from sportorg.common.otime import OTime
from sportorg.utils.time import int_to_otime, time_to_hhmmss

LOG_MSG = "HTTP Status: %s, Msg: %s"

RESULT_STATUS = [
    "NONE",
    "OK",
    "FINISHED",
    "DISQUALIFIED",
    "MISSING_PUNCH",
    "DID_NOT_FINISH",
    "ACTIVE",
    "INACTIVE",
    "OVERTIME",
    "SPORTING_WITHDRAWAL",
    "NOT_COMPETING",
    "MOVED",
    "MOVED_UP",
    "DID_NOT_START",
    "DID_NOT_ENTER",
    "CANCELLED",
    "OK",  # 'RESTORED' is 'OK'
    "DISQUALIFIED",  # MISSED_PENALTY_LAP
    "DISQUALIFIED",  # MULTI_DAY_ISSUE
]


class Orgeo:
    def __init__(self, session, url: str, user_agent: str = "SportOrg"):
        self.session = session
        self._url = url
        self._headers = {"User-Agent": user_agent}

    async def send(self, data):
        return await self.session.post(self._url, headers=self._headers, json=data)

    async def send_online_cp(self, chip, code, time):
        url = f"{self._url}&si={chip}&radio={code}&r={time}&fl=0"
        return await self.session.get(url, headers=self._headers)


def _get_obj(data, race_data, key, key_id):
    if key_id not in data or not data[key_id]:
        return
    for obj in race_data[key]:
        if data[key_id] == obj["id"]:
            return obj


def _get_group(data, race_data):
    return _get_obj(data, race_data, "groups", "group_id")


def _get_organization(data, race_data):
    return _get_obj(data, race_data, "organizations", "organization_id")


def _get_person(data, race_data):
    return _get_obj(data, race_data, "persons", "person_id")


def _get_result_by_person(data, race_data):
    for obj in race_data["results"]:
        if obj["person_id"] and data["id"] == obj["person_id"]:
            return obj


def _get_result_by_id(data, race_data):
    for obj in race_data["results"]:
        if obj["id"] and data["id"] == obj["id"]:
            return obj


def _get_person_obj(data, race_data, result=None):
    organization = "-"
    org = _get_organization(data, race_data)
    if org:
        organization = org["name"]
    group_name = "-"
    group = _get_group(data, race_data)
    if group:
        group_name = group["name"]
    obj = {
        "id": str(data["id"]),
        "ref_id": str(data["id"]),
        "bib": data["bib"],
        "group_name": group_name,
        "name": "{} {}".format(data["surname"], data["name"]),
        "organization": organization,
        # 'country_code': 'RUS',
        "card_number": data["card_number"],
        "national_code": None,
        "world_code": None,
        "out_of_competition": data["is_out_of_competition"],
        "start": round(data["start_time"] / 1000) if data["start_time"] else 0,
        "year": data["year"],
    }

    # TODO
    if "email" in data:
        obj["email"] = data["email"]
    if "phone" in data:
        obj["phone"] = data["phone"]

    is_relay = group and group["__type"] == 3 or race_data["data"]["race_type"] == 3
    if is_relay:
        # send relay fields only for relay events (requested by Ivan Churakoff)
        obj["relay_team"] = data["bib"] % 1000
        obj["lap"] = max(data["bib"] // 1000, 1)
    if result:
        obj["start"] = round(result["start_msec"] / 1000)

        if is_relay:
            obj["result_ms"] = round(
                result["result_relay_msec"] / 10
            )  # 1/100 sec - proprietary format
        else:
            obj["result_ms"] = round(
                result["result_msec"] / 10
            )  # 1/100 sec - proprietary format

        if race_data["settings"].get("result_processing_mode", "time") == "ardf":
            obj["score"] = result["scores_ardf"]
        elif race_data["settings"].get("result_processing_mode", "time") == "scores":
            obj["score"] = result["rogaine_score"]
            if result["rogaine_penalty"] > 0:
                obj["penalty"] = str(result["rogaine_penalty"])

        obj["result_status"] = (
            RESULT_STATUS[int(result["status"])]
            if -1 < int(result["status"]) < len(RESULT_STATUS)
            else "OK"
        )

        if len(result["splits"]):
            obj["splits"] = []
            splits = []
            for split in result["splits"]:
                if split["is_correct"] or race_data["settings"].get(
                    "live_sending_all_controls", False
                ):
                    splits.append(split)
            for i in range(len(splits)):
                # fmt: off
                """
                Orgeo Splits format:
                Option 	Type 	Description
                code 	string 	CP code
                time 	int 	seconds of current split - time from previous CP to this CP
                """
                # fmt: on
                current_split = {"code": splits[i]["code"]}
                end_time = splits[i]["time"] or 0
                if i > 0:
                    start_time = splits[i - 1]["time"] or 0
                else:
                    start_time = result["start_msec"]
                current_split["time"] = round((end_time - start_time) / 1000)
                obj["splits"].append(current_split)

            # add split from last control (or start if no splits) to finish
            end_time = result["finish_msec"]
            start_time = result["start_msec"]
            if len(splits) > 0:
                start_time = splits[-1]["time"] or 0
            current_split = {
                "code": "FIN",
                "time": round((end_time - start_time) / 1000),
            }
            obj["splits"].append(current_split)

            # add info about penalty (as string(20))
            if result["penalty_laps"] and result["penalty_laps"] > 0:
                obj["penalty"] = str(result["penalty_laps"])
            if result["penalty_time"] and result["penalty_time"] > 0:
                obj["penalty"] = time_to_hhmmss(OTime(msec=result["penalty_time"]))

    return obj


def make_nice(s):
    """
    Converts unicode point string to urf8
    :param s: unicode point string
    :return: utf8 string
    example:
    in: b'{"response":"OK: \\u00ab\\u043a\\u0440\\u043e\\u0441\\u0441-\\u0441\\u043f\\ ...
    out: b'{"response":"OK: «кросс-спринт» - Стартовый успешно загружен | Start list loaded"}'
    """
    return subn("(\\\\u[0-9a-f]{4})", lambda cp: chr(int(cp.groups()[0][3:], 16)), s)[0]


async def create(url, data, race_data, log, *, session):
    """
    data is Dict: Person, Result, Group, Course, Organization
    race_data is Dict: Race
    """
    o = Orgeo(session, url)
    is_start = False
    group_i = 0
    persons = []
    for item in data:
        if item["object"] == "Person":
            result_data = _get_result_by_person(item, race_data)
            persons.append(_get_person_obj(item, race_data, result_data))
        if item["object"] == "Group":
            group_i += 1
            for person_data in race_data["persons"]:
                if person_data["group_id"] and person_data["group_id"] == item["id"]:
                    result_data = _get_result_by_person(person_data, race_data)
                    persons.append(_get_person_obj(person_data, race_data, result_data))
        if item["object"] == "Organization":
            for person_data in race_data["persons"]:
                if (
                    person_data["organization_id"]
                    and person_data["organization_id"] == item["id"]
                ):
                    result_data = _get_result_by_person(person_data, race_data)
                    persons.append(_get_person_obj(person_data, race_data, result_data))
        elif item["object"] in [
            "Result",
            "ResultSportident",
            "ResultSportiduino",
            "ResultSFR",
            "ResultManual",
            "ResultRfidImpinj",
            "ResultSrpid",
        ]:
            person_data = _get_person(item, race_data)
            if person_data:
                persons.append(_get_person_obj(person_data, race_data, item))
    if group_i == len(race_data["groups"]):
        is_start = True
    if persons:
        obj_for_send: Dict[str, Any] = {"persons": persons}
        if is_start:
            obj_for_send["params"] = {"start_list": True}
        try:
            resp = await o.send(obj_for_send)

            result_txt = make_nice(str(await resp.text()))
            if resp.status != 200:
                log.error(LOG_MSG, resp.status, result_txt)
            else:
                log.info(LOG_MSG, resp.status, result_txt)

        except Exception as e:
            log.exception(e)


async def create_online_cp(url, data, race_data, log, *, session):
    """
    data is Dict: Results
    race_data is Dict: Race
    """

    if not race_data["settings"].get("live_cp_enabled", False):
        return

    o = Orgeo(session, url)

    for item in data:
        if item["object"] in [
            "Result",
            "ResultSportident",
            "ResultSportiduino",
            "ResultSFR",
            "ResultManual",
            "ResultRfidImpinj",
            "ResultSrpid",
        ]:
            try:
                res = _get_result_by_id(item, race_data)

                if res and race_data["settings"].get("live_cp_finish_enabled", True):
                    # send finish time as cp with specified code

                    card_number = res["card_number"]
                    if card_number == 0 and "person_id" in res:
                        person = _get_person(res, race_data)
                        if person:
                            card_number = person["card_number"]

                    if card_number > 0:
                        code = race_data["settings"].get("live_cp_code", "10")
                        finish_time = OTime.now()
                        if res["finish_time"] is not None:
                            finish_time = int_to_otime(
                                res["finish_time"] // 10
                            ).to_str()
                        resp = await o.send_online_cp(card_number, code, finish_time)
                        log.info(
                            "card=%s code=%s finish=%s",
                            str(card_number),
                            str(code),
                            str(finish_time),
                        )
                        result_txt = make_nice(str(await resp.text()))

                        if resp.status != 200:
                            log.error(LOG_MSG, resp.status, result_txt)
                        else:
                            log.info(LOG_MSG, resp.status, result_txt)
                    else:
                        log.info(LOG_MSG, 401, "Ignoring empty card number")

                if res and race_data["settings"].get("live_cp_splits_enabled", True):
                    # send split as cp, codes of cp to send are set by the list

                    card_number = res["card_number"]
                    if card_number == 0 and "person_id" in res:
                        person = _get_person(res, race_data)
                        if person:
                            card_number = person["card_number"]

                    if card_number > 0:
                        codes = (
                            race_data["settings"]
                            .get("live_cp_split_codes", "91,91,92")
                            .split(",")
                        )
                        for split in res["splits"]:
                            if split["code"] in codes:
                                split_time = int_to_otime(split["time"] // 10).to_str()
                                resp = await o.send_online_cp(
                                    card_number, split["code"], split_time
                                )
                                result_txt = make_nice(str(await resp.text()))
                                if resp.status != 200:
                                    log.error(LOG_MSG, resp.status, result_txt)
                                else:
                                    log.info(LOG_MSG, resp.status, result_txt)
                    else:
                        log.info(LOG_MSG, 401, "Ignoring empty card number")

            except Exception as e:
                log.exception(e)


async def delete(url, data, race_data, log, *, session):
    o = Orgeo(session, url)
    persons = []
    for item in data:
        if item["object"] == "Person":
            persons.append({"ref_id": item["id"]})
        elif item["object"] in [
            "Result",
            "ResultSportident",
            "ResultSportiduino",
            "ResultSFR",
            "ResultManual",
            "ResultRfidImpinj",
            "ResultSrpid",
        ]:
            person_data = _get_person(item, race_data)
            if person_data:
                persons.append({"ref_id": person_data["id"]})
    try:
        if persons:
            resp = await o.send({"persons": persons})
            result_txt = make_nice(str(await resp.text()))
            if resp.status != 200:
                log.error(LOG_MSG, resp.status, result_txt)
            else:
                log.info(LOG_MSG, resp.status, result_txt)

    except Exception as e:
        log.error("Error: %s", str(e))
