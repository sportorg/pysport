import sys
from PyQt5 import QtCore

from PyQt5.QtCore import QVariant, QAbstractTableModel

from sportorg.app.models import model
from sportorg.app.models.model import Person


class AbstractSportOrgTableModel (QAbstractTableModel):
    """
    Used to specify common table behavior
    """


class PersonTableModel(AbstractSportOrgTableModel):
    def __init__(self):
        super().__init__()
        self.model = None
        self.data = None
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
        return 4

    def data(self, index, role=None):
        if role == QtCore.Qt.DisplayRole:
            answer = str(index.row()) + " " + str(index.column())
            try:
                answer = self.get_person_data(index.row())[index.column()]
            except:
                print(sys.exc_info())

            return QVariant(answer)

        return QVariant()

    def get_person_data(self, position):

        # create data only at first call - do only 1 select
        if self.data is None:
            person = Person.select()
            self.data = []
            for i in person:
                self.data.append([i.name, i.surname, i.year, i.qual])

        current_person = self.data[position]
        return current_person
