import sys
import traceback

from PyQt5 import QtCore
from PyQt5.QtCore import QSortFilterProxyModel, QTime
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QLineEdit, QComboBox, QCompleter, QApplication, QDialog, \
    QPushButton, QTextEdit, QDateEdit, QTimeEdit, QSpinBox, QRadioButton, QGroupBox, QVBoxLayout

from sportorg.app.controllers.global_access import GlobalAccess
from sportorg.app.models.memory import race
from sportorg.app.plugins.utils.custom_controls import AdvComboBox
from sportorg.config import icon_dir

from sportorg.language import _




class SportidentPropertiesDialog(QDialog):
    def __init__(self, table=None, index=None):
        super().__init__()
        self.init_ui()

    def close_dialog(self):
        self.close()

    def init_ui(self):
        # self.setFixedWidth(500)
        self.setWindowTitle(_('SPORTident properties'))
        self.setWindowIcon(QIcon(icon_dir('sportident.png')))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.setToolTip(_('SPORTident Properties Window'))

        self.layout = QFormLayout(self)


        self.label_zero_time = QLabel(_('Zero time'))
        self.item_zero_time = QTimeEdit()
        self.item_zero_time.setDisplayFormat("HH:mm")
        default_time = QTime()
        default_time.setHMS(8, 0, 0)
        self.item_zero_time.setTime(default_time)
        self.layout.addRow(self.label_zero_time, self.item_zero_time)
        self.layout.addRow(self.label_zero_time, self.item_zero_time)

        self.start_group_box = QGroupBox(_('Start time'))
        self.start_layout = QFormLayout()
        self.item_start_protocol = QRadioButton(_('From protocol'))
        self.start_layout.addRow(self.item_start_protocol)
        self.item_start_station = QRadioButton(_('Start station'))
        self.start_layout.addRow(self.item_start_station)
        self.item_start_cp = QRadioButton(_('Control point'))
        self.item_start_cp_value = QSpinBox()
        self.item_start_cp_value.setValue(31)
        self.start_layout.addRow(self.item_start_cp, self.item_start_cp_value)
        self.item_start_gate = QRadioButton(_('Start gate'))
        self.start_layout.addRow(self.item_start_gate)
        self.start_group_box.setLayout(self.start_layout)
        self.layout.addRow(self.start_group_box)

        self.finish_group_box = QGroupBox(_('Finish time'))
        self.finish_layout = QFormLayout()
        self.item_finish_station = QRadioButton(_('Finish station'))
        self.finish_layout.addRow(self.item_finish_station)
        self.item_finish_cp = QRadioButton(_('Control point'))
        self.item_finish_cp_value = QSpinBox()
        self.item_finish_cp_value.setValue(90)
        self.finish_layout.addRow(self.item_finish_cp, self.item_finish_cp_value)
        self.item_finish_beam = QRadioButton(_('Light beam'))
        self.finish_layout.addRow(self.item_finish_beam)
        self.finish_group_box.setLayout(self.finish_layout)
        self.layout.addRow(self.finish_group_box)

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

        self.set_values_from_model()

        self.show()

    def set_values_from_model(self):
        obj = race()
        # self.item_main_title.setText(str(obj.get_setting('main_title')))
        # self.item_sub_title.setText(str(obj.get_setting('sub_title')))
        # self.item_location.setText(str(obj.get_setting('location')))
        # self.item_refery.setText(str(obj.get_setting('chief_referee')))
        # self.item_secretary.setText(str(obj.get_setting('secretary')))

    def apply_changes_impl(self):
        changed = False
        obj = race()

        # obj.set_setting('main_title', self.item_main_title.text())
        # obj.set_setting('sub_title', self.item_sub_title.toPlainText())
        # obj.set_setting('location', self.item_location.text())
        # obj.set_setting('chief_referee', self.item_refery.text())
        # obj.set_setting('secretary', self.item_secretary.text())

        if changed:
            win = self.get_main_window()

    def get_main_window(self):
        return GlobalAccess().get_main_window()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SportidentPropertiesDialog()
    sys.exit(app.exec_())
