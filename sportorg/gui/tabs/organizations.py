import logging

from PySide2 import QtWidgets

from sportorg.gui.dialogs.organization_edit import OrganizationEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.tabs.memory_model import OrganizationMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.models.memory import race


class OrganizationsTableView(TableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = []


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.organization_table = OrganizationsTableView(self)
        self.organization_layout = QtWidgets.QGridLayout(self)
        self.setup_ui()

    def setup_ui(self):

        self.organization_table.setObjectName('OrganizationTable')
        self.organization_table.setModel(OrganizationMemoryModel())

        def team_double_clicked(index):
            try:
                if index.row() < len(race().organizations):
                    dialog = OrganizationEditDialog(race().organizations[index.row()])
                    dialog.exec_()
                    GlobalAccess().get_main_window().refresh()
            except Exception as e:
                logging.error(str(e))

        self.organization_table.activated.connect(team_double_clicked)
        self.organization_layout.addWidget(self.organization_table)

    def get_table(self):
        return self.organization_table
