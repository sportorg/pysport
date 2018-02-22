import logging

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.gui.dialogs.entry_edit import EntryEditDialog
from sportorg.gui.global_access import GlobalAccess, NumberClicker
from sportorg.gui.tabs.memory_model import PersonMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.models.memory import race
from sportorg.models.start.relay import set_next_relay_number_to_person


class StartPreparationTableView(TableView):
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
        self.setup_ui()

    def keyPressEvent(self, e):
        key_numbers = [i for i in range(48, 58)]
        key = e.key()
        try:
            if key in key_numbers:
                self.EntryTable.set_start_group(NumberClicker().click(key_numbers.index(key)))
                GlobalAccess().get_main_window().refresh()
        except Exception as e:
            print(str(e))

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)
        self.entry_layout = QtWidgets.QGridLayout(self)
        self.entry_layout.setObjectName("entry_layout")

        self.EntryTable = StartPreparationTableView(self)
        self.EntryTable.setObjectName("EntryTable")

        self.EntryTable.setModel(PersonMemoryModel())
        self.EntryTable.setSortingEnabled(True)
        self.EntryTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        hor_header = self.EntryTable.horizontalHeader()
        assert (isinstance(hor_header, QHeaderView))
        hor_header.setSectionsMovable(True)
        hor_header.setDropIndicatorShown(True)
        hor_header.setSectionResizeMode(QHeaderView.Interactive)

        def entry_double_clicked(index):
            # show_edit_dialog(index)
            try:
                if index.row() < len(race().persons):
                    dialog = EntryEditDialog(race().persons[index.row()])
                    dialog.exec()
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

        self.EntryTable.activated.connect(entry_double_clicked)
        self.EntryTable.clicked.connect(entry_single_clicked)
        self.entry_layout.addWidget(self.EntryTable)

    def get_table(self):
        return self.EntryTable
