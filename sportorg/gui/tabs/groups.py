import logging

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.gui.dialogs.group_edit import GroupEditDialog
from sportorg.gui.tabs.memory_model import GroupMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.models.memory import race


class GroupsTableView(TableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = []


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setAcceptDrops(False)
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
        hor_header.setSectionResizeMode(QHeaderView.Interactive)

        ver_header = self.GroupTable.verticalHeader()
        ver_header.setSectionResizeMode(QHeaderView.ResizeToContents)

        def group_double_clicked(index):
            try:
                if index.row() < len(race().groups):
                    dialog = GroupEditDialog(race().groups[index.row()])
                    dialog.exec()
            except Exception as e:
                logging.error(str(e))

        self.GroupTable.activated.connect(group_double_clicked)
        self.group_layout.addWidget(self.GroupTable)

    def get_table(self):
        return self.GroupTable
