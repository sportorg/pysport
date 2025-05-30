import datetime
import logging

try:
    from PySide6 import QtCore, QtWidgets
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout
except ModuleNotFoundError:
    from PySide2 import QtCore, QtWidgets
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QDialog, QDialogButtonBox, QFormLayout

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox, AdvSpinBox, AdvTimeEdit
from sportorg.language import translate
from sportorg.models.constant import get_race_groups, get_race_teams
from sportorg.models.memory import Qualification, find, race


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

        empty_value = ""
        yes = translate("Yes")
        no = translate("No")

        max_field_width = 80

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

        self.year_checkbox = QtWidgets.QCheckBox(self)
        self.year_spinbox = AdvSpinBox(
            minimum=1900,
            maximum=datetime.datetime.now().year,
            max_width=max_field_width,
        )
        self.layout.addRow(self.year_checkbox, self.year_spinbox)

        self.qual_checkbox = QtWidgets.QCheckBox(self)
        self.qual_combo = AdvComboBox(self, val_list=Qualification.list_qual())
        self.qual_combo.setMaximumWidth(max_field_width)
        self.layout.addRow(self.qual_checkbox, self.qual_combo)

        self.bib_checkbox = QtWidgets.QCheckBox(self)
        self.bib_spinbox = AdvSpinBox(
            minimum=0, maximum=9999999, max_width=max_field_width
        )
        self.layout.addRow(self.bib_checkbox, self.bib_spinbox)

        self.world_code_checkbox = QtWidgets.QCheckBox(self)
        self.world_code_spinbox = AdvSpinBox(
            minimum=0, maximum=9999999, max_width=max_field_width
        )
        self.layout.addRow(self.world_code_checkbox, self.world_code_spinbox)

        self.national_code_checkbox = QtWidgets.QCheckBox(self)
        self.national_code_spinbox = AdvSpinBox(
            minimum=0, maximum=9999999, max_width=max_field_width
        )
        self.layout.addRow(self.national_code_checkbox, self.national_code_spinbox)

        self.card_checkbox = QtWidgets.QCheckBox(self)
        self.card_spinbox = AdvSpinBox(
            minimum=0, maximum=99999999, max_width=max_field_width
        )
        self.layout.addRow(self.card_checkbox, self.card_spinbox)

        self.start_time_checkbox = QtWidgets.QCheckBox(self)
        self.start_time_edit = AdvTimeEdit(
            display_format="hh:mm:ss", max_width=max_field_width
        )
        self.layout.addRow(self.start_time_checkbox, self.start_time_edit)

        self.start_group_checkbox = QtWidgets.QCheckBox(self)
        self.start_group_spinbox = AdvSpinBox(
            minimum=0, maximum=99, max_width=max_field_width
        )
        self.layout.addRow(self.start_group_checkbox, self.start_group_spinbox)

        self.comment_checkbox = QtWidgets.QCheckBox(self)
        self.comment_text = QtWidgets.QTextEdit()
        self.comment_text.setTabChangesFocus(True)
        self.comment_text.setMaximumHeight(44)
        self.layout.addRow(self.comment_checkbox, self.comment_text)

        self.rented_checkbox = QtWidgets.QCheckBox(self)
        self.rented_combobox = AdvComboBox(self)
        self.rented_combobox.addItem(yes)
        self.rented_combobox.addItem(no)
        self.rented_combobox.setEditable(False)
        self.rented_combobox.setMaximumWidth(50)
        self.layout.addRow(self.rented_checkbox, self.rented_combobox)

        self.paid_checkbox = QtWidgets.QCheckBox(self)
        self.paid_combobox = AdvComboBox(self)
        self.paid_combobox.addItem(yes)
        self.paid_combobox.addItem(no)
        self.paid_combobox.setEditable(False)
        self.paid_combobox.setMaximumWidth(50)
        self.layout.addRow(self.paid_checkbox, self.paid_combobox)

        self.out_of_competition_checkbox = QtWidgets.QCheckBox(self)
        self.out_of_competition_combobox = AdvComboBox(self)
        self.out_of_competition_combobox.addItem(yes)
        self.out_of_competition_combobox.addItem(no)
        self.out_of_competition_combobox.setEditable(False)
        self.out_of_competition_combobox.setMaximumWidth(50)
        self.layout.addRow(
            self.out_of_competition_checkbox, self.out_of_competition_combobox
        )

        self.personal_checkbox = QtWidgets.QCheckBox(self)
        self.personal_combobox = AdvComboBox(self)
        self.personal_combobox.addItem(yes)
        self.personal_combobox.addItem(no)
        self.personal_combobox.setEditable(False)
        self.personal_combobox.setMaximumWidth(50)
        self.layout.addRow(self.personal_checkbox, self.personal_combobox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.clicked.connect(self.accept)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.clicked.connect(self.reject)

        self.layout.addRow(button_box)

        self.translate_ui()

        self.show()

    def accept(self, *args, **kwargs):
        yes = translate("Yes")
        try:
            # apply mass edit here
            mv = GlobalAccess().get_main_window()
            selection = mv.get_selected_rows(mv.get_table_by_name("PersonTable"))
            if selection:
                obj = race()

                change_group = find(obj.groups, name=self.group_combo.currentText())
                change_team = find(
                    obj.organizations, name=self.team_combo.currentText()
                )
                change_year = int(self.year_spinbox.value())
                change_qual = Qualification.get_qual_by_name(
                    self.qual_combo.currentText()
                )
                change_bib = int(self.bib_spinbox.value())
                change_world_code = int(self.world_code_spinbox.value())
                change_national_code = int(self.national_code_spinbox.value())
                change_card_number = int(self.card_spinbox.value())
                change_start_time = self.start_time_edit.getOTime()
                start_group = int(self.start_group_spinbox.value())
                change_comment = self.comment_text.toPlainText()
                change_rented = self.rented_combobox.currentText() == yes
                change_paid = self.paid_combobox.currentText() == yes
                change_out_of_competition = (
                    self.out_of_competition_combobox.currentText() == yes
                )
                change_personal = self.personal_combobox.currentText() == yes

                for i in selection:
                    if i < len(obj.persons):
                        cur_person = obj.persons[i]

                        if self.group_checkbox.isChecked():
                            cur_person.group = change_group

                        if self.team_checkbox.isChecked():
                            cur_person.organization = change_team

                        if self.year_checkbox.isChecked():
                            cur_person.year = change_year

                        if self.qual_checkbox.isChecked():
                            cur_person.qual = change_qual

                        if self.bib_checkbox.isChecked():
                            cur_person.set_bib(change_bib)

                        if self.world_code_checkbox.isChecked():
                            cur_person.world_code = change_world_code

                        if self.national_code_checkbox.isChecked():
                            cur_person.national_code = change_national_code

                        if self.card_checkbox.isChecked():
                            cur_person.set_card_number(change_card_number)

                        if self.start_time_checkbox.isChecked():
                            cur_person.start_time = change_start_time

                        if self.start_group_checkbox.isChecked():
                            cur_person.start_group = start_group

                        if self.comment_checkbox.isChecked():
                            cur_person.comment = change_comment

                        if self.rented_checkbox.isChecked():
                            cur_person.is_rented_card = change_rented

                        if self.paid_checkbox.isChecked():
                            cur_person.is_paid = change_paid

                        if self.out_of_competition_checkbox.isChecked():
                            cur_person.is_out_of_competition = change_out_of_competition

                        if self.personal_checkbox.isChecked():
                            cur_person.is_personal = change_personal

        except Exception as e:
            logging.exception(e)

        super().accept(*args, **kwargs)

    def translate_ui(self):
        self.setWindowTitle(translate("Mass Edit Dialog"))
        self.group_checkbox.setText(translate("Group"))
        self.team_checkbox.setText(translate("Team"))
        self.year_checkbox.setText(translate("Year"))
        self.qual_checkbox.setText(translate("Qualification"))
        self.bib_checkbox.setText(translate("Bib"))
        self.world_code_checkbox.setText(translate("World code"))
        self.national_code_checkbox.setText(translate("National code"))
        self.card_checkbox.setText(translate("Card"))
        self.start_time_checkbox.setText(translate("Start time"))
        self.start_group_checkbox.setText(translate("Start group"))
        self.comment_checkbox.setText(translate("Comment"))
        self.rented_checkbox.setText(translate("rented card"))
        self.paid_checkbox.setText(translate("is paid"))
        self.out_of_competition_checkbox.setText(translate("out of competition"))
        self.personal_checkbox.setText(translate("personal participation"))

        self.button_ok.setText(translate("OK"))
        self.button_cancel.setText(translate("Cancel"))
