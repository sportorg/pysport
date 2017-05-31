import logging

import sys
import traceback

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.app.controller.dialogs.entry_edit import EntryEditDialog
from sportorg.app.models.memory_model import PersonMemoryModel, PersonProxyModel


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

        self.EntryTable = QtWidgets.QTableView(self)
        self.EntryTable.setObjectName("EntryTable")
        proxy_model = PersonProxyModel(self)
        proxy_model.setSourceModel(PersonMemoryModel())
        self.EntryTable.setModel(proxy_model)
        self.EntryTable.setSortingEnabled(True)
        self.EntryTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        hor_header = self.EntryTable.horizontalHeader()
        assert (isinstance(hor_header, QHeaderView))
        hor_header.setSectionsMovable(True)
        hor_header.setDropIndicatorShown(True)
        hor_header.setSectionResizeMode(QHeaderView.ResizeToContents)

        def entry_double_clicked(index):
            print('clicked on ' + str(index.row()))
            logging.info('clicked on ' + str(index.row()))
            # show_edit_dialog(index)
            try:
                dialog = EntryEditDialog(self.EntryTable, index)
            except:
                print(sys.exc_info())
                traceback.print_stack()

            dialog.exec()

        self.EntryTable.doubleClicked.connect(entry_double_clicked)
        self.entry_layout.addWidget(self.EntryTable)

    def get_table(self):
        return self.EntryTable
