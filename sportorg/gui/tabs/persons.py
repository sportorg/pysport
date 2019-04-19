import logging

from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import QAbstractTableModel
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

    def set_start_group(self, number, index):
        if -1 < index.row() < len(race().persons):
            person = race().persons[index.row()]
            person.start_group = number
            person.generate_cache()

    def keyPressEvent(self, e):
        key_numbers = [i for i in range(48, 58)]
        key = e.key()
        try:
            if key in key_numbers:
                index = self.currentIndex()
                self.set_start_group(NumberClicker().click(key_numbers.index(key)), index)
                self.update_row(index)
            else:
                super().keyPressEvent(e)
        except Exception as ex:
            print(str(ex))

class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.person_table = PersonsTableView(self)
        self.entry_layout = QtWidgets.QGridLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)

        self.person_table.setObjectName('PersonTable')

        self.person_table.setModel(PersonMemoryModel())
        self.person_table.setSortingEnabled(True)
        self.person_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        def entry_double_clicked(index):
            # show_edit_dialog(index)
            try:
                if index.row() < len(race().persons):
                    dialog = PersonEditDialog(race().persons[index.row()])
                    dialog.exec_()
                    GlobalAccess().get_main_window().refresh_table(GlobalAccess().get_main_window().get_result_table(),
                                                                   True)
            except Exception as e:
                logging.error(str(e))

        def entry_single_clicked(index):
            try:
                obj = race()
                if GlobalAccess().get_main_window().relay_number_assign:
                    if index.row() < len(obj.persons):
                        set_next_relay_number_to_person(obj.persons[index.row()])
                        self.person_table.update_row(index)

            except Exception as e:
                logging.error(str(e))

        self.person_table.activated.connect(entry_double_clicked)
        self.person_table.clicked.connect(entry_single_clicked)
        self.entry_layout.addWidget(self.person_table)

    def get_table(self):
        return self.person_table
