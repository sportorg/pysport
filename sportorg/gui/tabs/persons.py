import logging

from PySide2 import QtCore, QtWidgets
from PySide2.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.gui.dialogs.person_edit import PersonEditDialog
from sportorg.gui.global_access import GlobalAccess, NumberClicker
from sportorg.gui.tabs.memory_model import PersonMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.models.memory import race
from sportorg.models.start.relay import set_next_relay_number_to_person


class PersonsTableView(TableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = []

    def set_start_group(self, number):
        if -1 < self.currentIndex().row() < len(race().persons):
            person = race().persons[self.currentIndex().row()]
            person.start_group = number


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.person_table = PersonsTableView(self)
        self.entry_layout = QtWidgets.QGridLayout(self)
        self.setup_ui()

    def keyPressEvent(self, e):
        key_numbers = [i for i in range(48, 58)]
        key = e.key()
        try:
            if key in key_numbers:
                self.person_table.set_start_group(NumberClicker().click(key_numbers.index(key)))
                GlobalAccess().get_main_window().refresh()
        except Exception as e:
            print(str(e))

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)

        self.person_table.setObjectName('PersonTable')

        self.person_table.setModel(PersonMemoryModel())
        self.person_table.setSortingEnabled(True)
        self.person_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        hor_header = self.person_table.horizontalHeader()
        assert (isinstance(hor_header, QHeaderView))
        hor_header.setSectionsMovable(True)
        hor_header.setDropIndicatorShown(True)
        hor_header.setSectionResizeMode(QHeaderView.ResizeToContents)

        ver_header = self.person_table.verticalHeader()
        ver_header.setSectionResizeMode(QHeaderView.ResizeToContents)

        def entry_double_clicked(index):
            # show_edit_dialog(index)
            try:
                if index.row() < len(race().persons):
                    dialog = PersonEditDialog(race().persons[index.row()])
                    dialog.exec_()
                    GlobalAccess().get_main_window().refresh()
            except Exception as e:
                logging.error(str(e))

        def entry_single_clicked(index):
            try:
                obj = race()
                if obj.get_setting('relay_number_assign', False):
                    if index.row() < len(obj.persons):
                        set_next_relay_number_to_person(obj.persons[index.row()])

            except Exception as e:
                logging.error(str(e))

        self.person_table.activated.connect(entry_double_clicked)
        self.person_table.clicked.connect(entry_single_clicked)
        self.entry_layout.addWidget(self.person_table)

    def get_table(self):
        return self.person_table
