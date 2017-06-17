import sys

import logging

import time
import traceback

from PyQt5.QtCore import QVariant, QAbstractTableModel, Qt, QSortFilterProxyModel
from peewee import prefetch

from sportorg.app.models import model
from sportorg.app.models.model import Person, Participation, Group, Organization, ControlCard, Result


class AbstractSportOrgTableModel (QAbstractTableModel):
    """
    Used to specify common table behavior
    """


class PersonTableModel(AbstractSportOrgTableModel):
    def __init__(self):
        super().__init__()
        self.values = None
        self.count = None

    def rowCount(self, parent=None, *args, **kwargs):

        # calculate quantity only 1 time
        if self.count is None:
            try:
                m = model.Person
                if m.table_exists():
                    query = m.select()
                    self.count = query.count()

            except:
                print("Unexpected error:", sys.exc_info()[0])
                self.count = 300

        return self.count

    def columnCount(self, parent=None, *args, **kwargs):
        return 13

    def data(self, index, role=None):
        if role == Qt.DisplayRole:
            # start = time.time()
            # answer = str(index.row()) + ' ' + str(index.column())
            answer = ''
            try:
                answer = self.get_participation_data(index.row())[index.column()]
            except:
                print(sys.exc_info())
                traceback.print_stack()

            # end = time.time()
            # logging.info('Data() ' + str(index.row()) + ' ' + str(index.column()) + ': ' + str(end - start) + ' s')
            return QVariant(answer)

        return QVariant()

    def headerData(self, index, orientation, role=None):

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            columns = ['Surname', 'Name', 'Sex', 'Qualification', 'Group', 'Team', 'Year', 'Bib', 'Card', 'Rented card',
                       'Comment', 'World code', 'National code']
            return columns[index]
            # _translate = QtCore.QCoreApplication.translate
            # return _translate(columns[index]) TODO: add translation

    def get_participation_data(self, position):

        # create data only at first call - do only 1 select
        if self.values is None:
            start = time.time()
            # participation = Participation.select()
            #
            # query = (
            #     Participation
            #     .select(Participation, Person, Organization, Group, ControlCard)
            #     .join(Person)
            #     .join(Organization, JOIN_LEFT_OUTER)
            #     .switch(Participation)
            #     .join(Group, JOIN_LEFT_OUTER)
            #     .switch(Participation)
            #     .join(ControlCard, JOIN_LEFT_OUTER)
            #     .aggregate_rows()
            # )

            query = prefetch(
                Participation.select(),
                Person.select(),
                Organization.select(),
                Group.select(),
                ControlCard.select()
            )

            participation = query

            self.values = list()
            for i in participation:
                self.values.append(self.get_values_from_object(i))
            end = time.time()
            logging.info('Entry structure was created in ' + str(end - start) + ' s')

        ret = self.values[position]
        return ret

    def get_values_from_object(self, part):
        i = part
        assert (isinstance(i, Participation))
        person = i.person
        group = i.group
        group_name = ''
        if group is not None:
            assert (isinstance(group, Group))
            group_name = group.name
        team = person.team
        team_name = ''
        if team is not None:
            assert (isinstance(team, Organization))
            team_name = team.name
        card = i.control_card
        card_value = ''
        card_is_rented = ''
        if card is not None:
            assert (isinstance(card, ControlCard))
            card_value = card.value
            card.is_rented = card.is_rented
        assert (isinstance(person, Person))

        return list([
            person.surname,
            person.name,
            person.sex,
            person.qual,
            group_name,
            team_name,
            person.year,
            i.bib_number,
            card_value,
            card_is_rented,
            i.comment,
            person.world_code,
            person.national_code])

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)


class ResultTableModel(AbstractSportOrgTableModel):
    def __init__(self):
        super().__init__()
        self.values = None
        self.count = None

    def rowCount(self, parent=None, *args, **kwargs):

        # calculate quantity only 1 time
        if self.count is None:
            try:
                m = model.Result
                if m.table_exists():
                    query = m.select()
                    self.count = query.count()

            except:
                print("Unexpected error:", sys.exc_info()[0])
                self.count = 300

        return self.count

    def columnCount(self, parent=None, *args, **kwargs):
        return 11

    def data(self, index, role=None):
        if role == Qt.DisplayRole:
            # start = time.time()
            # answer = str(index.row()) + ' ' + str(index.column())
            answer = ''
            try:
                answer = self.get_participation_data(index.row())[index.column()]
            except:
                print(sys.exc_info())
                traceback.print_stack()

            # end = time.time()
            # logging.info('Data() ' + str(index.row()) + ' ' + str(index.column()) + ': ' + str(end - start) + ' s')
            return QVariant(answer)

        return QVariant()

    def headerData(self, index, orientation, role=None):

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            columns = ['Surname', 'Name', 'Group', 'Team', 'Bib', 'Start', 'Finish', 'Result', 'Status', 'Penalty',\
                       'Place']
            return columns[index]
            # _translate = QtCore.QCoreApplication.translate
            # return _translate(columns[index]) TODO: add translation

    def get_participation_data(self, position):

        # create data only at first call - do only 1 select
        if self.values is None:
            start = time.time()

            query = prefetch(
                Result.select(),
                Participation.select(),
                Person.select(),
                Organization.select(),
                Group.select()
            )

            result = query

            self.values = list()
            for i in result:
                self.values.append(self.get_values_from_object(i))
            end = time.time()
            logging.info('Entry structure was created in ' + str(end - start) + ' s')

        ret = self.values[position]
        return ret

    def get_values_from_object(self, result):
        i = result
        assert (isinstance(i, Result))
        participation = i.participation
        person = participation.person
        group = participation.group

        group_name = ''
        if group is not None:
            assert (isinstance(group, Group))
            group_name = group.name
        team = person.team
        team_name = ''
        if team is not None:
            assert (isinstance(team, Organization))
            team_name = team.name

        assert (isinstance(person, Person))

        result_time = 'res'
        # TODO calculate the result
        # start = datetime.strptime(i.start_time, '%H:%M:%S')
        # finish = datetime.strptime(i.finish_time, '%H:%M:%S')
        # result_time = finish - start


        return list([
            person.surname,
            person.name,
            group_name,
            team_name,
            participation.bib_number,
            i.start_time,
            i.finish_time,
            result_time,
            participation.status,
            i.penalty_time,
            'place'])

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)


class PersonProxyModel(QSortFilterProxyModel):

    def __init__(self, parent):
        super(PersonProxyModel, self).__init__(parent)
        self.filter_map = None
        self.filter_applied = False

    def clear_filter(self):
        self.filter_map = list()
        for i in range(self.sourceModel().columnCount()):
            self.filter_map.append('')
        self.filter_applied = False

    def set_filter_for_column(self, column, filter_string):
        if self.filter_map is None:
            self.clear_filter()
        self.filter_map[column] = filter_string
        self.invalidateFilter()
        self.filter_applied = True

    def filterAcceptsRow(self, row, index):
        if not self.filter_applied:
            return True
        try:
            source_model = self.sourceModel()
            size = source_model.columnCount()
            for i in range(size):
                if self.filter_map is not None and self.filter_map[i] is not None and self.filter_map[i] != '':
                    filter_string = self.filter_map[i]
                    cell = source_model.data(source_model.index(row, i), Qt.DisplayRole)
                    if str(cell.value()).find(filter_string) == -1:
                        return False
        except:
            print(sys.exc_info())
            traceback.print_stack()
        return True
