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
        cur_race = race()
        start_source = cur_race.get_setting('start_source')
        finish_source = cur_race.get_setting('finish_source')
        if not start_source:
            start_source = 'protocol'
        if not finish_source:
            finish_source = 'station'

        if start_source == 'protocol':
            self.item_start_protocol.setChecked(True)
        elif start_source == 'station':
            self.item_start_station.setChecked(True)
        elif start_source == 'cp':
            self.item_start_cp.setChecked(True)
        elif start_source == 'gate':
            self.item_start_gate.setChecked(True)

        if finish_source == 'station':
            self.item_finish_station.setChecked(True)
        elif finish_source == 'cp':
            self.item_finish_cp.setChecked(True)
        elif finish_source == 'beam':
            self.item_finish_beam.setChecked(True)

    def apply_changes_impl(self):
        changed = False
        obj = race()

        start_source=''
        if self.item_start_protocol.isChecked():
            start_source = 'protocol'
        if self.item_start_station.isChecked():
            start_source = 'station'
        if self.item_start_cp.isChecked():
            start_source = 'cp'
        if self.item_start_gate.isChecked():
            start_source = 'gate'

        finish_source = ''

        if self.item_finish_station.isChecked():
            finish_source = 'station'
        if self.item_finish_cp.isChecked():
            finish_source = 'cp'
        if self.item_finish_beam.isChecked():
            finish_source = 'beam'


        obj.set_setting('finish_source', finish_source)
        obj.set_setting('start_source', start_source)

        obj.set_setting('start_cp_number', self.item_start_cp_value.value())
        obj.set_setting('finish_cp_number', self.item_finish_cp_value.value())

        if changed:
            win = self.get_main_window()

    def get_main_window(self):
        return GlobalAccess().get_main_window()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SportidentPropertiesDialog()
    sys.exit(app.exec_())
