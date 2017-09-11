import logging
import traceback

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.app.controllers.dialogs.group_edit import GroupEditDialog
from sportorg.app.models.memory_model import GroupMemoryModel
from sportorg.app.controllers.tabs.table import TableView
from sportorg.app.controllers.global_access import GlobalAccess

from sportorg.language import _


class GroupsTableView(TableView):
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
        self.group_layout = QtWidgets.QGridLayout(self)
        self.group_layout.setObjectName("group_layout")

        self.GroupTable = GroupsTableView(self)
        self.GroupTable.setObjectName("GroupTable")
        self.GroupTable.setModel(GroupMemoryModel())
        self.GroupTable.setSortingEnabled(True)
        self.GroupTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        hor_header = self.GroupTable.horizontalHeader()
        assert (isinstance(hor_header, QHeaderView))
        hor_header.setSectionsMovable(True)
        hor_header.setDropIndicatorShown(True)
        hor_header.setSectionResizeMode(QHeaderView.ResizeToContents)

        def group_double_clicked(index):
            print('clicked on ' + str(index.row()))
            logging.info('clicked on ' + str(index.row()))

            try:
                 dialog = GroupEditDialog(self.GroupTable, index)
                 dialog.exec()
            except:
                traceback.print_exc()

        self.GroupTable.doubleClicked.connect(group_double_clicked)
        self.group_layout.addWidget(self.GroupTable)

    def get_table(self):
        return self.GroupTable
