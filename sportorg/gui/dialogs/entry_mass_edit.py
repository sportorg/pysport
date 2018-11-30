import logging

from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QDialog, QDialogButtonBox, QFormLayout

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.constant import get_race_teams, get_race_groups
from sportorg.models.memory import race, find


class MassEditDialog(QDialog):

    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):

        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)
        
        self.group_checkbox = QtWidgets.QCheckBox(self)
        self.group_combo = AdvComboBox(self)

        empty_value = ''

        group_list = get_race_groups()
        if empty_value not in group_list:
            group_list.insert(0, empty_value)
        self.group_combo.addItems(group_list)
        self.layout.addRow(self.group_checkbox, self.group_combo)

        self.team_checkbox = QtWidgets.QCheckBox(self)
        self.team_combo = AdvComboBox(self)
        team_list = get_race_teams()
        if empty_value not in team_list:
            team_list.insert(0, empty_value)
        self.team_combo.addItems(team_list)
        self.layout.addRow(self.team_checkbox, self.team_combo)

        self.start_group_checkbox = QtWidgets.QCheckBox(self)
        self.start_group_spinbox = QtWidgets.QSpinBox()
        self.start_group_spinbox.setMinimum(0)
        self.start_group_spinbox.setMaximum(99)
        self.layout.addRow(self.start_group_checkbox, self.start_group_spinbox)

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
            # apply mass edit here
            mv = GlobalAccess().get_main_window()
            selection = mv.get_selected_rows(mv.get_table_by_name('PersonTable'))
            if selection:
                obj = race()

                change_group = find(obj.groups, name=self.group_combo.currentText())
                change_team = find(obj.organizations, name=self.team_combo.currentText())
                start_group = int(self.start_group_spinbox.value())

                for i in selection:
                    if i < len(obj.persons):
                        cur_person = obj.persons[i]

                        if self.group_checkbox.isChecked():
                            cur_person.group = change_group

                        if self.team_checkbox.isChecked():
                            cur_person.organization = change_team

                        if self.start_group_checkbox.isChecked():
                            cur_person.start_group = start_group

        except Exception as e:
            logging.exception(e)

        super().accept(*args, **kwargs)

    def retranslate_ui(self):
        self.setWindowTitle(_("Mass Edit Dialog"))
        self.group_checkbox.setText(_("Group"))
        self.team_checkbox.setText(_("Team"))
        self.start_group_checkbox.setText(_("Start group"))

        self.button_ok.setText(_('OK'))
        self.button_cancel.setText(_('Cancel'))
