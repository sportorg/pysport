import logging

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.gui.dialogs.organization_edit import OrganizationEditDialog
from sportorg.gui.tabs.memory_model import TeamMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.models.memory import race


class TeamsTableView(TableView):
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
        self.team_layout = QtWidgets.QGridLayout(self)
        self.team_layout.setObjectName("team_layout")

        self.TeamTable = TeamsTableView(self)
        self.TeamTable.setObjectName("TeamTable")

        self.TeamTable.setModel(TeamMemoryModel())
        self.TeamTable.setSortingEnabled(True)
        self.TeamTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        hor_header = self.TeamTable.horizontalHeader()
        assert (isinstance(hor_header, QHeaderView))
        hor_header.setSectionsMovable(True)
        hor_header.setDropIndicatorShown(True)
        hor_header.setSectionResizeMode(QHeaderView.Interactive)

        def team_double_clicked(index):
            try:
                if index.row() < len(race().organizations):
                    dialog = OrganizationEditDialog(race().organizations[index.row()])
                    dialog.exec()
            except Exception as e:
                logging.error(str(e))

        self.TeamTable.activated.connect(team_double_clicked)
        self.team_layout.addWidget(self.TeamTable)

    def get_table(self):
        return self.TeamTable
