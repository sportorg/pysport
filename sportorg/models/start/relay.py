from sportorg.gui.global_access import GlobalAccess
from sportorg.models.memory import race, Person, find


def get_last_relay_number_protocol():
    obj = race()
    max_num = 1000
    for i in obj.persons:
        cur_num = i.bib
        if cur_num > max_num:
            max_num = cur_num
    return max_num


def get_next_relay_number(num):

    last_num = num
    if last_num == 1000:
        return 1001

    leg_count = get_leg_count()
    last_leg = last_num // 1000

    if last_leg >= leg_count:
        return 1000 + last_num % 1000 + 1
    else:
        return last_num + 1000


def get_next_relay_number_protocol():
    return get_next_relay_number(get_last_relay_number_protocol())


def get_next_relay_number_setting():
    obj = race()
    settings_num = obj.get_setting('relay_next_number', 1001)
    # protocol_num = get_next_relay_number_protocol()
    return settings_num


def set_next_relay_number(num):
    obj = race()
    obj.set_setting('relay_next_number', num)


def get_leg_count():
    obj = race()
    return obj.data.relay_leg_count


def set_next_relay_number_to_person(person):
    assert isinstance(person, Person)
    person.bib = get_next_relay_number_setting()
    set_next_relay_number(get_next_relay_number(person.bib))
    GlobalAccess().get_main_window().refresh()


def get_team_result(person):
    bib = person.bib % 1000
    relay_team = find(race().relay_teams, bib_number=bib)
    if relay_team:
        if relay_team.get_lap_finished() == get_leg_count():
            return relay_team.get_time()