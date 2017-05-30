import sys


import traceback
from datetime import timedelta

import time
from PyQt5.QtCore import QVariant, QAbstractTableModel, Qt, QSortFilterProxyModel

from sportorg.app.models.memory import race, Result



class AbstractSportOrgMemoryModel (QAbstractTableModel):
    """
    Used to specify common table behavior
    """


class PersonMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()

    def rowCount(self, parent=None, *args, **kwargs):
        ret = len(race().persons)
        return ret

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
        return self.get_value_from_object(race().persons[position])

    def get_value_from_object(self, object):
        ret = list()
        person = object

        ret.append(person.surname)
        ret.append(person.name)
        ret.append(person.sex)
        ret.append(person.qual)
        if person.group is None:
            ret.append('')
        else:
            ret.append(person.group.name)
        if person.organization is None:
            ret.append('')
        else:
            ret.append(person.organization.name)
        ret.append(person.year)
        ret.append(person.bib)
        ret.append(person.card_number)
        ret.append('rented stub')
        ret.append('comment stub')
        ret.append(person.world_code)
        ret.append(person.national_code)
        return ret

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)


class ResultMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.values = None
        self.count = None

    def rowCount(self, parent=None, *args, **kwargs):
        return len(race().results)

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
        ret = self.get_values_from_object(race().results[position])
        return ret

    def get_values_from_object(self, result):
        i = result
        assert (isinstance(i, Result))
        person = result.person

        result_time = (i.finish_time - i.start_time)
        assert (isinstance(result_time, timedelta))

        return list([
            person.surname,
            person.name,
            person.group.name,
            person.organization.name,
            person.bib,
            i.start_time.strftime('%H:%M:%S'),
            i.finish_time.strftime('%H:%M:%S'),
            str(result_time),
            i.status,
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
