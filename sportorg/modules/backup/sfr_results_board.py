import os

from sportorg.models.memory import race


def dump(file, *, compress=False):
    r = race()
    sep = "\t"

    is_rogaine = r.get_setting("result_processing_mode", "time") == "scores"
    is_ardf = r.get_setting("result_processing_mode", "time") == "ardf"
    is_relay = r.is_relay()

    for result in r.results:
        if result.person:
            line = get_srb_line_for_result(result, sep, is_rogaine, is_ardf, is_relay)
            if compress:
                file.write(bytes(line, "utf-8"))
            else:
                file.write(line)
    file.flush()
    os.fsync(file.fileno())


def get_srb_line_for_result(result, sep, is_rogaine, is_ardf, is_relay) -> str:
    person = result.person
    if person:
        uid = str(person.bib)
        group = ""
        if person.group:
            group = person.group.name

        scores_for_sort = 99999
        if is_rogaine:
            scores_for_sort -= result.rogaine_score
        elif is_ardf:
            scores_for_sort -= result.scores_ardf
        leg_for_sort = 0
        if is_relay:
            leg_for_sort = int(person.bib) // 1000
        sort = (
            ("0" + str(leg_for_sort))[-2:] + str(scores_for_sort) + result.get_result()
        )

        place = "1"
        if not result.is_status_ok():
            place = "0"
        if person.is_out_of_competition:
            place = "0"
        res = result.get_result()
        name = person.full_name
        team = ""
        if person.organization:
            team = person.organization.name
        line = (
            uid
            + sep
            + group
            + sep
            + sort
            + sep
            + place
            + sep
            + name
            + sep
            + team
            + sep
            + res
            + "\n"
        )
        return line
    return ""
