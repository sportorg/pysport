import logging

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.app.gui.dialogs.group_edit import GroupEditDialog
from sportorg.app.models.memory_model import GroupMemoryModel
from sportorg.app.gui.tabs.table import TableView
from sportorg.app.gui.global_access import GlobalAccess

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
            logging.debug('clicked on ' + str(index.row()))

            try:
                 dialog = GroupEditDialog(self.GroupTable, index)
                 dialog.exec()
            except Exception as e:
                logging.exception(e)

        self.GroupTable.activated.connect(group_double_clicked)
        self.group_layout.addWidget(self.GroupTable)

    def get_table(self):
        return self.GroupTable
