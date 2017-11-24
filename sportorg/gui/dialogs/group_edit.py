import logging
import sys

from PyQt5.QtCore import QModelIndex
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QLineEdit, QApplication, QDialog, \
    QPushButton, QSpinBox, QTimeEdit, QCheckBox

from sportorg import config
from sportorg.gui.dialogs.group_ranking import GroupRankingDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.memory import race, Group, find, Sex, Limit
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.utils.time import time_to_qtime, time_to_otime


def get_courses():
    ret = []
    try:
        for i in race().courses:
            ret.append(i.name)
        return ret
    except Exception as e:
        logging.exception(str(e))


def get_sexes():
    return [Sex.MF.get_title(), Sex.M.get_title(), Sex.F.get_title()]


class GroupEditDialog(QDialog):
    def __init__(self, table=None, index=None):
        super().__init__()
        self.init_ui()
        if table is not None:
            self.set_values_from_table(table, index)

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle(_('Group properties'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_name = QLabel(_('Name'))
        self.item_name = QLineEdit()
        self.layout.addRow(self.label_name, self.item_name)

        self.label_full_name = QLabel(_('Full name'))
        self.item_full_name = QLineEdit()
        self.layout.addRow(self.label_full_name, self.item_full_name)

        self.label_course = QLabel(_('Course'))
        self.item_course = AdvComboBox()
        self.item_course.addItems(get_courses())
        self.layout.addRow(self.label_course, self.item_course)

        self.label_sex = QLabel(_('Sex'))
        self.item_sex = AdvComboBox()
        self.item_sex.addItems(get_sexes())
        self.layout.addRow(self.label_sex, self.item_sex)

        self.label_age_min = QLabel(_('Min age'))
        self.item_age_min = QSpinBox()
        self.layout.addRow(self.label_age_min, self.item_age_min)

        self.label_age_max = QLabel(_('Max age'))
        self.item_age_max = QSpinBox()
        self.layout.addRow(self.label_age_max, self.item_age_max)

        self.label_max_time = QLabel(_('Max time'))
        self.item_max_time = QTimeEdit()
        self.item_max_time.setDisplayFormat("hh:mm:ss")
        self.layout.addRow(self.label_max_time, self.item_max_time)

        self.label_corridor = QLabel(_('Start corridor'))
        self.item_corridor = QSpinBox()
        self.layout.addRow(self.label_corridor, self.item_corridor)

        self.label_corridor_order = QLabel(_('Order in corridor'))
        self.item_corridor_order = QSpinBox()
        self.layout.addRow(self.label_corridor_order, self.item_corridor_order)

        self.label_start_interval = QLabel(_('Start interval'))
        self.item_start_interval = QTimeEdit()
        self.item_start_interval.setDisplayFormat("hh:mm:ss")
        self.layout.addRow(self.label_start_interval, self.item_start_interval)

        self.label_price = QLabel(_('Start fee'))
        self.item_price = QSpinBox()
        self.item_price.setSingleStep(50)
        self.item_price.setMaximum(Limit.PRICE)
        self.layout.addRow(self.label_price, self.item_price)

        self.rank_checkbox = QCheckBox(_('Rank calculation'))
        self.rank_button = QPushButton(_('Configuration'))
        self.layout.addRow(self.rank_checkbox, self.rank_button)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(str(e))
            self.close()

        self.button_ok = QPushButton(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

        self.show()

    def set_values_from_table(self, table, index):
        self.table = table
        self.current_index = index

        assert (isinstance(index, QModelIndex))
        orig_index_int = index.row()

        current_object = race().groups[orig_index_int]
        assert (isinstance(current_object, Group))
        self.current_object = current_object

        self.item_name.setText(current_object.name)

        if current_object.long_name:
            self.item_full_name.setText(current_object.long_name)
        if current_object.course:
            self.item_course.setCurrentText(current_object.course.name)
        if current_object.sex:
            self.item_sex.setCurrentText(current_object.sex.get_title())
        if current_object.min_age:
            self.item_age_min.setValue(current_object.min_age)
        if current_object.max_age:
            self.item_age_max.setValue(current_object.max_age)
        if current_object.max_time:
            self.item_max_time.setTime(time_to_qtime(current_object.max_time))
        if current_object.start_interval:
            self.item_start_interval.setTime(time_to_qtime(current_object.start_interval))
        if current_object.start_corridor:
            self.item_corridor.setValue(current_object.start_corridor)
        if current_object.order_in_corridor:
            self.item_corridor_order.setValue(current_object.order_in_corridor)
        if current_object.price:
            self.item_price.setValue(current_object.price)

        self.rank_checkbox.setChecked(current_object.ranking.is_active)

        def rank_configuration():
            group = current_object
            GroupRankingDialog(group).exec()

        self.rank_button.clicked.connect(rank_configuration)

    def apply_changes_impl(self):
        changed = False
        org = self.current_object
        assert (isinstance(org, Group))

        if org.name != self.item_name.text():
            org.name = self.item_name.text()
            changed = True

        if org.long_name != self.item_full_name.text():
            org.long_name = self.item_full_name.text()
            changed = True

        if (org.course is not None and org.course.name != self.item_course.currentText()) \
                or (org.course is None and len(self.item_course.currentText()) > 0):
            org.course = find(race().courses, name=self.item_course.currentText())
            changed = True

        if str(org.sex) != self.item_sex.currentText():
            org.sex = Sex.get_by_title(self.item_sex.currentText())
            changed = True

        if org.min_age != self.item_age_min.value():
            org.min_age = self.item_age_min.value()
            changed = True

        if org.max_age != self.item_age_max.value():
            org.max_age = self.item_age_max.value()
            changed = True

        if org.start_corridor != self.item_corridor.value():
            org.start_corridor = self.item_corridor.value()
            changed = True

        if org.order_in_corridor != self.item_corridor_order.value():
            org.order_in_corridor = self.item_corridor_order.value()
            changed = True

        if org.price != self.item_price.value():
            org.price = self.item_price.value()
            changed = True

        time = time_to_otime(self.item_start_interval.time())
        if org.start_interval != time:
            org.start_interval = time
            changed = True

        time = time_to_otime(self.item_max_time.time())

        if org.max_time != time:
            org.max_time = time
            changed = True

        if org.ranking.is_active != self.rank_checkbox.isChecked():
            org.ranking.is_active = self.rank_checkbox.isChecked()
            changed = True

        if changed:
            ResultCalculation().set_rank(org)
            GlobalAccess().get_main_window().refresh()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GroupEditDialog()
    sys.exit(app.exec_())
