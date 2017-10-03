import sys
import traceback

from PyQt5.QtCore import QModelIndex
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QLineEdit, QApplication, QDialog, \
    QPushButton, QSpinBox, QTimeEdit

from sportorg.app.controllers.global_access import GlobalAccess
from sportorg.app.models.memory import race, Group, find
from sportorg.app.modules.utils.custom_controls import AdvComboBox
from sportorg.app.modules.utils.utils import datetime2qtime, qtime2datetime

from sportorg.language import _
from sportorg import config


def get_courses():
    ret = []
    try:
        for i in race().courses:
            ret.append(i.name)
        return ret
    except:
        return ['']


def get_sexes():
    return ['', 'M', 'F']


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
        self.setToolTip(_('Group Edit Window'))

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

        self.label_first_number = QLabel(_('First number'))
        self.item_first_number = QSpinBox()
        self.item_first_number.setMaximum(1000000)
        self.layout.addRow(self.label_first_number, self.item_first_number)

        self.label_price = QLabel(_('Start fee'))
        self.item_price = QSpinBox()
        self.item_price.setSingleStep(50)
        self.item_price.setMaximum(100000000)
        self.layout.addRow(self.label_price, self.item_price)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except:
                print(sys.exc_info())
                traceback.print_exc()
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

        if current_object.long_name is not None:
            self.item_full_name.setText(current_object.long_name)
        if current_object.course is not None:
            self.item_course.setCurrentText(current_object.course.name)
        if current_object.sex is not None:
            self.item_sex.setCurrentText(current_object.sex)
        if current_object.min_age is not None:
            self.item_age_min.setValue(current_object.min_age)
        if current_object.max_age is not None:
            self.item_age_max.setValue(current_object.max_age)
        if current_object.max_time is not None:
            self.item_max_time.setTime(datetime2qtime(current_object.max_time))
        if current_object.start_interval is not None:
            self.item_start_interval.setTime(datetime2qtime(current_object.start_interval))
        if current_object.start_corridor is not None:
            self.item_corridor.setValue(current_object.start_corridor)
        if current_object.order_in_corridor is not None:
            self.item_corridor_order.setValue(current_object.order_in_corridor)
        if current_object.price is not None:
            self.item_price.setValue(current_object.price)
        if current_object.first_number is not None:
            self.item_first_number.setValue(current_object.first_number)

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

        if org.sex != self.item_sex.currentText():
            org.sex = self.item_sex.currentText()
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

        if org.first_number != self.item_first_number.value():
            org.first_number = self.item_first_number.value()
            changed = True

        time = qtime2datetime(self.item_start_interval.time())
        if org.start_interval != time:
            org.start_interval = time
            changed = True

        time = qtime2datetime(self.item_max_time.time())
        if org.max_time != time:
            org.max_time = time
            changed = True

        if changed:
            self.get_parent_window().refresh()

    def get_parent_window(self):
        return GlobalAccess().get_main_window()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GroupEditDialog()
    sys.exit(app.exec_())
