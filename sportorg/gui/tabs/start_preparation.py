import logging

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.gui.dialogs.entry_edit import EntryEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.tabs.memory_model import PersonMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.language import _
from sportorg.models.memory import race
from sportorg.models.start.relay import set_next_relay_number_to_person


class StartPreparationTableView(TableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = [
            (_("Add object"), GlobalAccess().add_object),
            (_('Delete'), GlobalAccess().get_main_window().delete_object)
        ]


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

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
            logging.debug('Entered ' + str(index.row()))
            # show_edit_dialog(index)
            try:
                if index.row() < len(race().persons):
                    dialog = EntryEditDialog(self.EntryTable, index)
                    dialog.exec()
            except Exception as e:
                logging.exception(str(e))

        def entry_single_clicked(index):
            logging.debug('Clicked ' + str(index.row()))
            try:
                obj = race()
                if obj.get_setting('relay_number_assign', False):
                    if index.row() < len(obj.persons):
                        set_next_relay_number_to_person(obj.persons[index.row()])

            except Exception as e:
                logging.exception(str(e))

        self.EntryTable.activated.connect(entry_double_clicked)
        self.EntryTable.clicked.connect(entry_single_clicked)
        self.entry_layout.addWidget(self.EntryTable)

    def get_table(self):
        return self.EntryTable
