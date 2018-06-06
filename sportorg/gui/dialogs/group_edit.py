import logging
from datetime import date

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QLineEdit, QDialog, QPushButton, QSpinBox, QTimeEdit, QCheckBox, \
    QDialogButtonBox

from sportorg import config
from sportorg.gui.dialogs.group_ranking import GroupRankingDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.constant import get_race_courses
from sportorg.models.memory import race, Group, find, Sex, Limit, RaceType
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.modules.teamwork import Teamwork
from sportorg.utils.time import time_to_qtime, time_to_otime


class GroupEditDialog(QDialog):
    def __init__(self, group, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        assert (isinstance(group, Group))
        self.current_object = group
        self.is_new = is_new
        self.time_format = 'hh:mm:ss'

    def exec(self):
        self.init_ui()
        self.set_values_from_model()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Group properties'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_name = QLabel(_('Name'))
        self.item_name = QLineEdit()
        self.item_name.textChanged.connect(self.check_name)
        self.layout.addRow(self.label_name, self.item_name)

        self.label_full_name = QLabel(_('Full name'))
        self.item_full_name = QLineEdit()
        self.layout.addRow(self.label_full_name, self.item_full_name)

        self.label_course = QLabel(_('Course'))
        self.item_course = AdvComboBox()
        self.item_course.addItems(get_race_courses())
        self.layout.addRow(self.label_course, self.item_course)

        self.label_is_any_course = QLabel(_('Is any course'))
        self.item_is_any_course = QCheckBox()
        self.item_is_any_course.stateChanged.connect(self.is_any_course_update)
        self.layout.addRow(self.label_is_any_course, self.item_is_any_course)

        self.label_sex = QLabel(_('Sex'))
        self.item_sex = AdvComboBox()
        self.item_sex.addItems(Sex.get_titles())
        self.layout.addRow(self.label_sex, self.item_sex)

        self.label_age_min = QLabel(_('Min age'))
        self.item_age_min = QSpinBox()
        # self.layout.addRow(self.label_age_min, self.item_age_min)

        self.label_age_max = QLabel(_('Max age'))
        self.item_age_max = QSpinBox()
        # self.layout.addRow(self.label_age_max, self.item_age_max)

        self.label_year_min = QLabel(_('Min year'))
        self.item_year_min = QSpinBox()
        self.item_year_min.setMaximum(date.today().year)
        self.item_year_min.editingFinished.connect(self.year_change)
        self.layout.addRow(self.label_year_min, self.item_year_min)

        self.label_year_max = QLabel(_('Max year'))
        self.item_year_max = QSpinBox()
        self.item_year_max.setMaximum(date.today().year)
        self.item_year_max.editingFinished.connect(self.year_change)
        self.layout.addRow(self.label_year_max, self.item_year_max)

        self.label_max_time = QLabel(_('Max time'))
        self.item_max_time = QTimeEdit()
        self.item_max_time.setDisplayFormat(self.time_format)
        self.layout.addRow(self.label_max_time, self.item_max_time)

        self.label_corridor = QLabel(_('Start corridor'))
        self.item_corridor = QSpinBox()
        self.layout.addRow(self.label_corridor, self.item_corridor)

        self.label_corridor_order = QLabel(_('Order in corridor'))
        self.item_corridor_order = QSpinBox()
        self.layout.addRow(self.label_corridor_order, self.item_corridor_order)

        self.label_start_interval = QLabel(_('Start interval'))
        self.item_start_interval = QTimeEdit()
        self.item_start_interval.setDisplayFormat(self.time_format)
        self.layout.addRow(self.label_start_interval, self.item_start_interval)

        self.label_price = QLabel(_('Start fee'))
        self.item_price = QSpinBox()
        self.item_price.setSingleStep(50)
        self.item_price.setMaximum(Limit.PRICE)
        self.layout.addRow(self.label_price, self.item_price)

        self.type_label = QLabel(_('Type'))
        self.type_combo = AdvComboBox()
        self.type_combo.addItems(RaceType.get_titles())
        self.layout.addRow(self.type_label, self.type_combo)

        self.rank_checkbox = QCheckBox(_('Rank calculation'))
        self.rank_button = QPushButton(_('Configuration'))
        self.layout.addRow(self.rank_checkbox, self.rank_button)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.error(str(e))
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()
        self.button_ok.setFocus()

    def check_name(self):
        name = self.item_name.text()
        self.button_ok.setDisabled(False)
        if name and name != self.current_object.name:
            group = find(race().groups, name=name)
            if group:
                self.button_ok.setDisabled(True)

    def year_change(self):
        """
        Convert 2 digits of year to 4
        2 -> 2002
        11 - > 2011
        33 -> 1933
        56 -> 1956
        98 - > 1998
        0 -> 0 exception!
        """
        widget = self.sender()
        assert isinstance(widget, QSpinBox)
        year = widget.value()
        if 0 < year < 100:
            cur_year = date.today().year
            new_year = cur_year - cur_year % 100 + year
            if new_year > cur_year:
                new_year -= 100
            widget.setValue(new_year)

    def is_any_course_update(self):
        if self.item_is_any_course.isChecked():
            self.item_course.setDisabled(True)
        else:
            self.item_course.setDisabled(False)

    def set_values_from_model(self):

        self.item_name.setText(self.current_object.name)

        if self.current_object.long_name:
            self.item_full_name.setText(self.current_object.long_name)
        if self.current_object.course:
            self.item_course.setCurrentText(self.current_object.course.name)
        if self.current_object.sex:
            self.item_sex.setCurrentText(self.current_object.sex.get_title())
        if self.current_object.min_age:
            self.item_age_min.setValue(self.current_object.min_age)
        if self.current_object.max_age:
            self.item_age_max.setValue(self.current_object.max_age)
        if self.current_object.min_year:
            self.item_year_min.setValue(self.current_object.min_year)
        if self.current_object.max_year:
            self.item_year_max.setValue(self.current_object.max_year)
        if self.current_object.max_time:
            self.item_max_time.setTime(time_to_qtime(self.current_object.max_time))
        if self.current_object.start_interval:
            self.item_start_interval.setTime(time_to_qtime(self.current_object.start_interval))
        if self.current_object.start_corridor:
            self.item_corridor.setValue(self.current_object.start_corridor)
        if self.current_object.order_in_corridor:
            self.item_corridor_order.setValue(self.current_object.order_in_corridor)
        if self.current_object.price:
            self.item_price.setValue(self.current_object.price)

        self.item_is_any_course.setChecked(self.current_object.is_any_course)
        self.rank_checkbox.setChecked(self.current_object.ranking.is_active)
        self.type_combo.setCurrentText(race().get_type(self.current_object).get_title())

        def rank_configuration():
            group = self.current_object
            GroupRankingDialog(group).exec()

        self.rank_button.clicked.connect(rank_configuration)

    def apply_changes_impl(self):
        group = self.current_object
        assert (isinstance(group, Group))
        if self.is_new:
            race().groups.insert(0, group)

        if group.name != self.item_name.text():
            group.name = self.item_name.text()

        if group.long_name != self.item_full_name.text():
            group.long_name = self.item_full_name.text()

        if (group.course is not None and group.course.name != self.item_course.currentText()) \
                or (group.course is None and len(self.item_course.currentText()) > 0):
            group.course = find(race().courses, name=self.item_course.currentText())

        if group.sex.get_title() != self.item_sex.currentText():
            group.sex = Sex(self.item_sex.currentIndex())

        if group.min_age != self.item_age_min.value():
            group.min_age = self.item_age_min.value()

        if group.max_age != self.item_age_max.value():
            group.max_age = self.item_age_max.value()

        if group.min_year != self.item_year_min.value():
            group.min_year = self.item_year_min.value()

        if group.max_year != self.item_year_max.value():
            group.max_year = self.item_year_max.value()

        if group.start_corridor != self.item_corridor.value():
            group.start_corridor = self.item_corridor.value()

        if group.order_in_corridor != self.item_corridor_order.value():
            group.order_in_corridor = self.item_corridor_order.value()

        if group.price != self.item_price.value():
            group.price = self.item_price.value()

        time = time_to_otime(self.item_start_interval.time())
        if group.start_interval != time:
            group.start_interval = time

        time = time_to_otime(self.item_max_time.time())

        if group.max_time != time:
            group.max_time = time

        if group.ranking.is_active != self.rank_checkbox.isChecked():
            group.ranking.is_active = self.rank_checkbox.isChecked()

        t = RaceType.get_by_name(self.type_combo.currentText())
        selected_type = t if t is not None else group.get_type()
        if group.get_type() != selected_type:
            group.set_type(selected_type)

        group.is_any_course = self.item_is_any_course.isChecked()

        ResultCalculation(race()).set_rank(group)
        GlobalAccess().get_main_window().refresh()
        Teamwork().send(group.to_dict())
