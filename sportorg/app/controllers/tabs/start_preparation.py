import logging

import sys
import traceback

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.app.controllers.dialogs.entry_edit import EntryEditDialog
from sportorg.app.models.memory_model import PersonMemoryModel
from sportorg.app.controllers.tabs.table import TableView
from sportorg.app.controllers.global_access import GlobalAccess

from sportorg.language import _


class StartPreparationTableView(TableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = [
            (_("Add object"), GlobalAccess().add_object)
        ]


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setToolTip("")
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
        hor_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        hor_header.setSectionResizeMode(QHeaderView.Interactive)

        def entry_double_clicked(index):
            print('clicked on ' + str(index.row()))
            logging.info('clicked on ' + str(index.row()))
            # show_edit_dialog(index)
            try:
                dialog = EntryEditDialog(self.EntryTable, index)
            except:
                print(sys.exc_info())
                traceback.print_exc()

            dialog.exec()

        self.EntryTable.doubleClicked.connect(entry_double_clicked)
        self.entry_layout.addWidget(self.EntryTable)

    def get_table(self):
        return self.EntryTable

    def get_parent_window(self):
        return self.parent
