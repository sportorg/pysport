import logging

from PySide2 import QtCore, QtWidgets
from PySide2.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.gui.dialogs.group_edit import GroupEditDialog
from sportorg.gui.global_access import GlobalAccess
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
        self.group_table = GroupsTableView(self)
        self.group_layout = QtWidgets.QGridLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)

        self.group_table.setObjectName('GroupTable')
        self.group_table.setModel(GroupMemoryModel())
        self.group_table.setSortingEnabled(True)
        self.group_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        def group_double_clicked(index):
            try:
                if index.row() < len(race().groups):
                    dialog = GroupEditDialog(race().groups[index.row()])
                    dialog.exec_()
            except Exception as e:
                logging.error(str(e))

        self.group_table.activated.connect(group_double_clicked)
        self.group_layout.addWidget(self.group_table)

    def get_table(self):
        return self.group_table
