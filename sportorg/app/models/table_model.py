import sys
from PyQt5 import QtCore

from PyQt5.QtCore import QModelIndex, QVariant, QAbstractTableModel

from sportorg.app.models import model
from sportorg.app.models.model import Person


class AbstractSportOrgTableModel (QAbstractTableModel):
    """
    Used to specify common table behavior
    """

class PersonTableModel (AbstractSportOrgTableModel):

    def __init__(self):
        super().__init__()
        self.model = None

    def rowCount(self, parent=None, *args, **kwargs):
        try:
            m = model.Person
            if m.table_exists():
                query = m.select()
                count = query.count()
                return count

        except AttributeError as e:
            print("Unexpected error:", sys.exc_info()[0])

        count = 30
        return count


    def columnCount(self, parent=None, *args, **kwargs):
        return 4

    def data(self, index, role=None):
        if role == QtCore.Qt.DisplayRole:
            answer = str(index.row()) + " " + str(index.column())
            try:
                answer = self.getPersonData(index.row())[index.column()]
            except:
                print(sys.exc_info())

            return QVariant(answer);

        return QVariant();


    def getPersonData(self, position):
        ret = list()
        person = Person.select()[position]
        ret.append(person.name)
        ret.append(person.surname)
        ret.append(person.year)
        ret.append(person.qual)
        return ret