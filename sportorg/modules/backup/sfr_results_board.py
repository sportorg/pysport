import os

from sportorg.models.memory import race


def dump(file, *, compress=False):
    r = race()
    sep = "\t"
    for result in r.results:
        person = result.person
        if person:
            uid = str(person.bib)
            group = ""
            if person.group:
                group = person.group.name
            sort = result.get_result()
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
            line = uid + sep + group + sep + sort + sep + place + sep + name + sep + team + sep + res + "\n"
            file.write(line)
    file.flush()
    os.fsync(file.fileno())
