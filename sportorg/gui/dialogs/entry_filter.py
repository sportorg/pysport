import logging

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QTableView

from sportorg import config
from sportorg.gui.dialogs import entry_edit
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _


class DialogFilter(QDialog):

    def __init__(self, table=None):
        super().__init__(GlobalAccess().get_main_window())
        if table is not None:
            self.table = table

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setObjectName("filter_dialog")
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowIcon(QIcon(config.ICON))
        self.resize(300, 200)
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.grid_layout = QtWidgets.QGridLayout(self)
        self.grid_layout.setObjectName("gridLayout")
        
        self.group_label = QtWidgets.QLabel(self)
        self.group_label.setObjectName("group_label")
        self.grid_layout.addWidget(self.group_label, 0, 0, 1, 4)

        self.group_combo = AdvComboBox(self)
        self.group_combo.setObjectName("group_combo")
        self.group_combo.addItem('')
        self.group_combo.addItems(entry_edit.get_groups())
        self.grid_layout.addWidget(self.group_combo, 0, 1, 1, 4)

        self.team_label = QtWidgets.QLabel(self)
        self.team_label.setObjectName("team_label")
        self.grid_layout.addWidget(self.team_label, 1, 0, 1, 4)

        self.team_combo = AdvComboBox(self)
        self.team_combo.setObjectName("team_combo")
        self.team_combo.addItem('')
        self.team_combo.addItems(entry_edit.get_teams())
        self.grid_layout.addWidget(self.team_combo, 1, 1, 1, 4)

        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.button_box.setObjectName("button_box")
        self.grid_layout.addWidget(self.button_box, 2, 0, 1, 2)

        self.retranslate_ui()
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.show()

    def accept(self):

        try:
            # apply filter here
            if self.table is not None:
                assert (isinstance(self.table, QTableView))
                proxy_model = self.table.model()
                proxy_model.clear_filter()

                group_column = 4
                team_column = 5

                if GlobalAccess().get_current_tab_index() == 1:
                    group_column = 2
                    team_column = 3

                proxy_model.set_filter_for_column(group_column, self.group_combo.currentText())
                proxy_model.set_filter_for_column(team_column, self.team_combo.currentText())

                proxy_model.apply_filter()

                GlobalAccess().get_main_window().refresh()
        except Exception as e:
            logging.exception(str(e))

        self.destroy()

    def reject(self):
        self.destroy()

    def retranslate_ui(self):
        self.setWindowTitle(_("Filter Dialog"))
        self.group_label.setText(_("Group"))
        self.team_label.setText(_("Team"))
