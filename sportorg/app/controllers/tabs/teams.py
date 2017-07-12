import logging

import sys
import traceback

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.app.controllers.dialogs.organization_edit import OrganizationEditDialog
from sportorg.app.models.memory_model import PersonProxyModel, TeamMemoryModel


class Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setup_ui()
        self.parent = parent

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setToolTip("")
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)
        self.team_layout = QtWidgets.QGridLayout(self)
        self.team_layout.setObjectName("team_layout")

        self.TeamTable = QtWidgets.QTableView(self)
        self.TeamTable.setObjectName("TeamTable")
        proxy_model = PersonProxyModel(self)
        proxy_model.setSourceModel(TeamMemoryModel())
        self.TeamTable.setModel(proxy_model)
        self.TeamTable.setSortingEnabled(True)
        self.TeamTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        hor_header = self.TeamTable.horizontalHeader()
        assert (isinstance(hor_header, QHeaderView))
        hor_header.setSectionsMovable(True)
        hor_header.setDropIndicatorShown(True)
        hor_header.setSectionResizeMode(QHeaderView.ResizeToContents)

        def team_double_clicked(index):
            print('Team: clicked on ' + str(index.row()))
            try:
                dialog = OrganizationEditDialog(self.TeamTable, index, self.get_parent_window())
                dialog.exec()
            except:
                print(sys.exc_info())
                traceback.print_exc()

            logging.info('Team: clicked on ' + str(index.row()))

        self.TeamTable.doubleClicked.connect(team_double_clicked)
        self.team_layout.addWidget(self.TeamTable)

    def get_table(self):
        return self.TeamTable()

    def get_parent_window(self):
        return self.parent
