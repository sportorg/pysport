import logging

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.app.gui.dialogs.entry_edit import EntryEditDialog
from sportorg.app.models.memory import race
from sportorg.app.models.memory_model import PersonMemoryModel
from sportorg.app.gui.tabs.table import TableView
from sportorg.app.gui.global_access import GlobalAccess

from sportorg.language import _


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
            logging.debug('Clicked on ' + str(index.row()))
            # show_edit_dialog(index)
            try:
                if index.row() < len(race().persons):
                    dialog = EntryEditDialog(self.EntryTable, index)
                    dialog.exec()
            except Exception as e:
                logging.exception(str(e))

        self.EntryTable.activated.connect(entry_double_clicked)
        self.entry_layout.addWidget(self.EntryTable)

    def get_table(self):
        return self.EntryTable
