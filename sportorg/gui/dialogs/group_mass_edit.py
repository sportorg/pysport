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
from sportorg.models.constant import get_race_courses
from sportorg.models.memory import RaceType, find, race


class GroupMassEditDialog(QDialog):
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

        yes = translate("Yes")
        no = translate("No")
        cur_year = datetime.datetime.now().year

        max_field_width = 80

        course_list = get_race_courses()
        self.course_checkbox = QtWidgets.QCheckBox(self)
        self.course_combobox = AdvComboBox(self, val_list=course_list)
        self.layout.addRow(self.course_checkbox, self.course_combobox)

        self.any_course_checkbox = QtWidgets.QCheckBox(self)
        self.any_course_combobox = AdvComboBox(self, val_list={yes, no}, max_width=50)
        self.any_course_combobox.setEditable(False)
        self.layout.addRow(self.any_course_checkbox, self.any_course_combobox)

        self.min_year_checkbox = QtWidgets.QCheckBox(self)
        self.min_year_spinbox = AdvSpinBox(
            minimum=0, maximum=cur_year, max_width=max_field_width
        )
        self.layout.addRow(self.min_year_checkbox, self.min_year_spinbox)

        self.max_year_checkbox = QtWidgets.QCheckBox(self)
        self.max_year_spinbox = AdvSpinBox(
            minimum=0, maximum=cur_year, max_width=max_field_width
        )
        self.layout.addRow(self.max_year_checkbox, self.max_year_spinbox)

        self.time_limit_checkbox = QtWidgets.QCheckBox(self)
        self.time_limit_edit = AdvTimeEdit(
            display_format="hh:mm:ss", max_width=max_field_width
        )
        self.layout.addRow(self.time_limit_checkbox, self.time_limit_edit)

        self.start_corridor_checkbox = QtWidgets.QCheckBox(self)
        self.start_corridor_spinbox = AdvSpinBox(minimum=0, max_width=max_field_width)
        self.layout.addRow(self.start_corridor_checkbox, self.start_corridor_spinbox)

        self.order_in_corridor_checkbox = QtWidgets.QCheckBox(self)
        self.order_in_corridor_spinbox = AdvSpinBox(
            minimum=0, max_width=max_field_width
        )
        self.layout.addRow(
            self.order_in_corridor_checkbox, self.order_in_corridor_spinbox
        )

        self.start_interval_checkbox = QtWidgets.QCheckBox(self)
        self.start_interval_edit = AdvTimeEdit(
            display_format="hh:mm:ss", max_width=max_field_width
        )
        self.layout.addRow(self.start_interval_checkbox, self.start_interval_edit)

        self.fee_checkbox = QtWidgets.QCheckBox(self)
        self.fee_spinbox = AdvSpinBox(minimum=0, max_width=max_field_width)
        self.layout.addRow(self.fee_checkbox, self.fee_spinbox)

        course_types = RaceType.get_titles()
        self.type_checkbox = QtWidgets.QCheckBox(self)
        self.type_checkbox.stateChanged.connect(self.on_race_type_changed)
        self.type_combobox = AdvComboBox(self, val_list=course_types)
        self.type_combobox.currentIndexChanged.connect(self.on_race_type_changed)
        self.layout.addRow(self.type_checkbox, self.type_combobox)

        self.comp_type_checkbox = QtWidgets.QCheckBox(self)
        self.comp_type_checkbox.stateChanged.connect(self.on_race_type_changed)
        self.comp_type_combobox = AdvComboBox(self, val_list={yes, no}, max_width=50)
        self.comp_type_combobox.currentIndexChanged.connect(self.on_race_type_changed)
        self.comp_type_combobox.setEditable(False)

        self.layout.addRow(self.comp_type_checkbox, self.comp_type_combobox)

        self.best_placing_checkbox = QtWidgets.QCheckBox(self)
        self.best_placing_combobox = AdvComboBox(self, val_list={yes, no}, max_width=50)
        self.best_placing_combobox.setEditable(False)

        self.layout.addRow(self.best_placing_checkbox, self.best_placing_combobox)

        self.ranking_checkbox = QtWidgets.QCheckBox(self)
        self.ranking_combobox = AdvComboBox(self, val_list={yes, no}, max_width=50)
        self.ranking_combobox.setEditable(False)
        self.layout.addRow(self.ranking_checkbox, self.ranking_combobox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.clicked.connect(self.accept)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.clicked.connect(self.reject)

        self.layout.addRow(button_box)

        self.on_race_type_changed()
        self.translate_ui()

        self.show()

    def on_race_type_changed(self):
        yes = translate("Yes")
        text = self.type_combobox.currentText()
        is_relay = RaceType.get_by_name(text) == RaceType.RELAY
        is_relay_type_enabled = self.type_checkbox.isChecked() and is_relay
        is_comp_type_all_russian = (
            is_relay_type_enabled
            and self.comp_type_checkbox.isChecked()
            and self.comp_type_combobox.currentText() == yes
        )

        self.comp_type_checkbox.setEnabled(is_relay_type_enabled)
        self.comp_type_combobox.setEnabled(is_relay_type_enabled)

        self.best_placing_checkbox.setEnabled(is_comp_type_all_russian)
        self.best_placing_combobox.setEnabled(is_comp_type_all_russian)

    def accept(self, *args, **kwargs):
        yes = translate("Yes")
        try:
            # apply mass edit here
            mv = GlobalAccess().get_main_window()
            selection = mv.get_selected_rows(mv.get_table_by_name("GroupTable"))
            if selection:
                obj = race()

                change_course = find(
                    obj.courses, name=self.course_combobox.currentText()
                )
                change_any_course = self.any_course_combobox.currentText() == yes
                change_min_year = int(self.min_year_spinbox.value())
                change_max_year = int(self.max_year_spinbox.value())
                change_time_limit = self.time_limit_edit.getOTime()
                change_corridor = int(self.start_corridor_spinbox.value())
                change_order_in_corridor = int(self.order_in_corridor_spinbox.value())
                change_start_interval = self.start_interval_edit.getOTime()
                change_fee = int(self.fee_spinbox.value())
                change_type = RaceType.get_by_name(self.type_combobox.currentText())
                change_comp_type = self.comp_type_combobox.currentText() == yes
                change_placing_type = (
                    change_comp_type and self.best_placing_combobox.currentText() == yes
                )
                change_ranking = self.ranking_combobox.currentText() == yes

                for i in selection:
                    if i < len(obj.persons):
                        cur_group = obj.groups[i]

                        if self.course_checkbox.isChecked():
                            cur_group.course = change_course

                        if self.any_course_checkbox.isChecked():
                            cur_group.is_any_course = change_any_course

                        if self.min_year_checkbox.isChecked():
                            cur_group.min_year = change_min_year

                        if self.max_year_checkbox.isChecked():
                            cur_group.max_year = change_max_year

                        if self.time_limit_checkbox.isChecked():
                            cur_group.max_time = change_time_limit

                        if self.start_corridor_checkbox.isChecked():
                            cur_group.start_corridor = change_corridor

                        if self.order_in_corridor_checkbox.isChecked():
                            cur_group.order_in_corridor = change_order_in_corridor

                        if self.start_interval_checkbox.isChecked():
                            cur_group.start_interval = change_start_interval

                        if self.fee_checkbox.isChecked():
                            cur_group.price = change_fee

                        if self.type_checkbox.isChecked():
                            cur_group.set_type(change_type)

                        if self.comp_type_checkbox.isChecked():
                            cur_group.is_all_russian_competition = change_comp_type

                        if self.best_placing_checkbox.isChecked():
                            cur_group.is_best_team_placing_mode = change_placing_type

                        if self.ranking_checkbox.isChecked():
                            cur_group.ranking.is_active = change_ranking

        except Exception as e:
            logging.exception(e)

        super().accept(*args, **kwargs)

    def translate_ui(self):
        self.setWindowTitle(translate("Mass Edit Dialog"))
        self.course_checkbox.setText(translate("Course"))
        self.any_course_checkbox.setText(translate("Is any course"))
        self.min_year_checkbox.setText(translate("Min year"))
        self.max_year_checkbox.setText(translate("Max year"))
        self.time_limit_checkbox.setText(translate("Max time"))
        self.start_corridor_checkbox.setText(translate("Start corridor"))
        self.order_in_corridor_checkbox.setText(translate("Order in corridor"))
        self.start_interval_checkbox.setText(translate("Start interval"))
        self.fee_checkbox.setText(translate("Start fee"))
        self.type_checkbox.setText(translate("Type"))
        self.comp_type_checkbox.setText(translate("All-Russian competition"))
        self.best_placing_checkbox.setText(translate("Best team placing"))
        self.ranking_checkbox.setText(translate("Rank calculation"))

        self.button_ok.setText(translate("OK"))
        self.button_cancel.setText(translate("Cancel"))
