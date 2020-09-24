import logging

from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QDialog, QDialogButtonBox, QFormLayout

from sportorg import config
from sportorg.gui.dialogs.person_edit import PersonEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import translate
from sportorg.models.constant import get_race_groups, get_race_teams


class DialogFilter(QDialog):
    def __init__(self, table=None):
        super().__init__(GlobalAccess().get_main_window())
        if table:
            self.table = table

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.group_label = QtWidgets.QLabel(self)

        self.group_combo = AdvComboBox(self)
        self.group_combo.addItem('')
        self.group_combo.addItems(get_race_groups())
        self.layout.addRow(self.group_label, self.group_combo)

        self.team_label = QtWidgets.QLabel(self)

        self.team_combo = AdvComboBox(self)
        self.team_combo.addItem('')
        self.team_combo.addItems(get_race_teams())
        self.layout.addRow(self.team_label, self.team_combo)

        self.max_rows_count_label = QtWidgets.QLabel(self)

        self.max_rows_count_spin_box = QtWidgets.QSpinBox(self)
        self.max_rows_count_spin_box.setMaximum(100000)
        self.max_rows_count_spin_box.setValue(5000)
        self.layout.addRow(self.max_rows_count_label, self.max_rows_count_spin_box)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.clicked.connect(self.accept)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.clicked.connect(self.reject)

        self.layout.addRow(button_box)

        self.retranslate_ui()

        self.show()

    def accept(self, *args, **kwargs):

        try:
            # apply filter here
            if self.table:
                proxy_model = self.table.model()
                proxy_model.clear_filter()
                proxy_model.max_rows_count = self.max_rows_count_spin_box.value()

                group_column = 4
                team_column = 5

                if GlobalAccess().get_main_window().current_tab == 1:
                    group_column = 2
                    team_column = 3

                proxy_model.set_filter_for_column(
                    group_column, self.group_combo.currentText()
                )
                proxy_model.set_filter_for_column(
                    team_column, self.team_combo.currentText()
                )

                proxy_model.apply_filter()

                PersonEditDialog.GROUP_NAME = self.group_combo.currentText()
                PersonEditDialog.ORGANIZATION_NAME = self.team_combo.currentText()
        except Exception as e:
            logging.error(str(e))

        super().accept(*args, **kwargs)

    def retranslate_ui(self):
        self.setWindowTitle(translate('Filter Dialog'))
        self.group_label.setText(translate('Group'))
        self.team_label.setText(translate('Team'))
        self.max_rows_count_label.setText(translate('Max rows count'))
        self.button_ok.setText(translate('OK'))
        self.button_cancel.setText(translate('Cancel'))
