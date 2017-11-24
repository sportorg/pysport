from typing import _qualname

from sportorg.app.gui.global_access import GlobalAccess
from sportorg.app.models import memory
from sportorg.app.models.memory import Qualification
from sportorg.lib.winorient.wdb import write_wdb
from .wdb import WinOrientBinary
from sportorg.lib.winorient import wo


def import_csv(source):
    wo_csv = wo.parse_csv(source)
    race = memory.race()

    for group_name in wo_csv.groups:
        group = memory.create(memory.Group, name=group_name, long_name=group_name)
        race.groups.append(group)

    for team_name in wo_csv.teams:
        org = memory.create(memory.Organization, name=team_name)
        race.organizations.append(org)

    for person_dict in wo_csv.data:
        person = memory.create(
            memory.Person,
            **person_dict,
            group=memory.find(race.groups, name=person_dict['group_name']),
            organization=memory.find(race.organizations, name=person_dict['team_name']),
            qual=Qualification(int(person_dict['qual_id']))
        )
        race.persons.append(person)


def import_wo_wdb(file_name):
    wb = WinOrientBinary(file=file_name)
    # wb.run()
    wb.create_objects()


def export_wo_wdb(file_name):
    wb = WinOrientBinary()

    GlobalAccess().clear_filters(False)
    wdb_object = wb.export()
    GlobalAccess().apply_filters()

    write_wdb(wdb_object, file_name)
