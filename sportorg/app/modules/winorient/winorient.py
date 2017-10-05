import logging

import time

from sportorg.app.controllers.global_access import GlobalAccess
from sportorg.language import _
from sportorg.app.models import model
from sportorg.app.models import memory
from sportorg.lib.winorient.wdb import write_wdb
from .wdb import WinOrientBinary
from sportorg.lib.winorient import wo
from PyQt5 import QtWidgets


def import_csv_to_model(source):
    wo_csv = wo.parse_csv(source)

    data_group = [{'name': group, 'long_name': group} for group in wo_csv.groups]
    model_group = {}
    with model.database_proxy.atomic():
        for data_dict in data_group:
            group = model.Group.create(**data_dict)
            model_group[group.name] = group.id

    data_team = [{'name': team} for team in wo_csv.teams]
    model_team = {}
    with model.database_proxy.atomic():
        for data_dict in data_team:
            org = model.Organization.create(**data_dict)
            model_team[org.name] = org.id

    data_person = []
    for p in wo_csv.data:
        p['group'] = model_group[p['group']]
        p['team'] = model_team[p['team']]
        data_person.append(p)
    with model.database_proxy.atomic():
        for data_dict in data_person:
            person = model.Person.create(**data_dict)
            participation = {
                "person": person,
                "group": data_dict['group']
            }
            if data_dict['card']:
                participation['control_card'] = model.ControlCard.create(
                    name="SPORTIDENT",
                    value=data_dict['card'],
                    person=person
                )

            model.Participation.create(**participation)

    return True


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
            organization=memory.find(race.organizations, name=person_dict['team_name'])
        )
        race.persons.append(person)


def import_wo_csv():
    file_name = QtWidgets.QFileDialog.getOpenFileName(None, 'Open CSV Winorient file',
                                        '', "CSV Winorient (*.csv)")[0]
    if file_name is not '':
        import_csv(file_name)
        GlobalAccess().get_main_window().init_model()


def import_wo_wdb():
    file_name = QtWidgets.QFileDialog.getOpenFileName(None, 'Open WDB Winorient file',
                                        '', "WDB Winorient (*.wdb)")[0]
    if file_name is not '':
        try:
            wb = WinOrientBinary(file=file_name)
            # wb.run()
            wb.create_objects()
            GlobalAccess().get_main_window().init_model()
        except Exception as e:
            logging.exception(str(e))


def export_wo_wdb():
    file_name = QtWidgets.QFileDialog.getSaveFileName(None, _('Save As WDB file'),
                                                      '/sportorg_export_' + str(time.strftime("%Y%m%d")),
                                                      _("WDB file (*.wdb)"))[0]
    if file_name is not '':
        try:
            wb = WinOrientBinary()

            GlobalAccess().clear_filters(False)
            wdb_object = wb.export()
            GlobalAccess().apply_filters()

            write_wdb(wdb_object, file_name)

        except Exception as e:
            logging.exception(str(e))
