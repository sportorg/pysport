import logging

from PyQt5.QtCore import QTime
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QDialog, \
    QPushButton, QTimeEdit, QSpinBox, QRadioButton, QGroupBox, QCheckBox, QGridLayout

from sportorg.app.gui.global_access import GlobalAccess
from sportorg.app.models.memory import race, Config
from sportorg.config import icon_dir

from sportorg.language import _


class SportidentPropertiesDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def close_dialog(self):
        self.close()

    def init_ui(self):
        # self.setFixedWidth(500)
        self.setWindowTitle(_('SPORTident settings'))
        self.setWindowIcon(QIcon(icon_dir('sportident.png')))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_zero_time = QLabel(_('Zero time'))
        self.item_zero_time = QTimeEdit()
        self.item_zero_time.setDisplayFormat("HH:mm")
        self.item_zero_time.setMaximumSize(60, 20)
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
        self.item_start_cp_value.setMaximumSize(60, 20)
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
        self.item_finish_cp_value.setMaximumSize(60, 20)
        self.finish_layout.addRow(self.item_finish_cp, self.item_finish_cp_value)
        self.item_finish_beam = QRadioButton(_('Light beam'))
        self.finish_layout.addRow(self.item_finish_beam)
        self.finish_group_box.setLayout(self.finish_layout)
        self.layout.addRow(self.finish_group_box)

        self.chip_reading_box = QGroupBox(_('Assigning a chip when reading'))
        self.chip_reading_layout = QFormLayout()
        self.chip_reading_off = QRadioButton(_('Off'))
        self.chip_reading_layout.addRow(self.chip_reading_off)
        self.chip_reading_unknown = QRadioButton(_('Only unknown members'))
        self.chip_reading_layout.addRow(self.chip_reading_unknown)
        self.chip_reading_always = QRadioButton(_('Always'))
        self.chip_reading_layout.addRow(self.chip_reading_always)
        self.chip_reading_box.setLayout(self.chip_reading_layout)
        # self.layout.addRow(self.chip_reading_box)

        self.repeated_reading_box = QGroupBox(_('Repeated reading'))
        self.repeated_reading_layout = QFormLayout()
        self.repeated_reading_rewrite = QRadioButton(_('Rewrite'))
        self.repeated_reading_layout.addRow(self.repeated_reading_rewrite)
        self.repeated_reading_add = QRadioButton(_('Add'))
        self.repeated_reading_layout.addRow(self.repeated_reading_add)
        self.repeated_reading_keep_all_version = QRadioButton(_('Keep all versions'))
        self.repeated_reading_layout.addRow(self.repeated_reading_keep_all_version)
        self.repeated_reading_box.setLayout(self.repeated_reading_layout)
        # self.layout.addRow(self.repeated_reading_box)

        self.assignment_mode = QCheckBox(_('Assignment mode'))
        # self.assignment_mode.stateChanged.connect(self.on_assignment_mode)
        # self.layout.addRow(self.assignment_mode)

        self.auto_connect = QCheckBox(_('Auto connect to station'))
        self.layout.addRow(self.auto_connect)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(e)
            self.close()

        bottom = QGridLayout()
        self.button_ok = QPushButton(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        bottom.addWidget(self.button_ok, 0, 0)
        bottom.addWidget(self.button_cancel, 0, 1)
        self.layout.addRow(bottom)

        self.set_values_from_model()

        self.show()

    def on_assignment_mode(self):
        mode = False
        if self.assignment_mode.isChecked():
            mode = True
        self.start_group_box.setDisabled(mode)
        self.finish_group_box.setDisabled(mode)
        self.chip_reading_box.setDisabled(mode)
        self.repeated_reading_box.setDisabled(mode)

    def set_values_from_model(self):
        cur_race = race()
        zero_time = cur_race.get_setting('sportident_zero_time', (8, 0, 0))
        start_source = cur_race.get_setting('sportident_start_source', 'protocol')
        finish_source = cur_race.get_setting('sportident_finish_source', 'station')
        assign_chip_reading = cur_race.get_setting('sportident_assign_chip_reading', 'off')
        repeated_reading = cur_race.get_setting('sportident_repeated_reading', 'rewrite')
        assignment_mode = cur_race.get_setting('sportident_assignment_mode', False)

        self.item_zero_time.setTime(QTime(zero_time[0], zero_time[1]))

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

        if assign_chip_reading == 'off':
            self.chip_reading_off.setChecked(True)
        elif assign_chip_reading == 'only_unknown_members':
            self.chip_reading_unknown.setChecked(True)
        elif assign_chip_reading == 'always':
            self.chip_reading_always.setChecked(True)

        if repeated_reading == 'rewrite':
            self.repeated_reading_rewrite.setChecked(True)
        elif repeated_reading == 'add':
            self.repeated_reading_add.setChecked(True)
        elif repeated_reading == 'keep_all_versions':
            self.repeated_reading_keep_all_version.setChecked(True)

        self.assignment_mode.setChecked(assignment_mode)
        self.auto_connect.setChecked(Config.get('autoconnect'))

    def apply_changes_impl(self):
        changed = False
        obj = race()

        start_source = 'protocol'
        if self.item_start_station.isChecked():
            start_source = 'station'
        elif self.item_start_cp.isChecked():
            start_source = 'cp'
        elif self.item_start_gate.isChecked():
            start_source = 'gate'

        finish_source = 'station'
        if self.item_finish_cp.isChecked():
            finish_source = 'cp'
        elif self.item_finish_beam.isChecked():
            finish_source = 'beam'

        assign_chip_reading = 'off'
        if self.chip_reading_unknown.isChecked():
            assign_chip_reading = 'only_unknown_members'
        elif self.chip_reading_always.isChecked():
            assign_chip_reading = 'always'

        repeated_reading = 'rewrite'
        if self.repeated_reading_add.isChecked():
            repeated_reading = 'add'
        elif self.repeated_reading_keep_all_version.isChecked():
            repeated_reading = 'keep_all_versions'

        obj.set_setting('sportident_zero_time', (
            self.item_zero_time.time().hour(),
            self.item_zero_time.time().minute(),
            0
        ))

        obj.set_setting('sportident_finish_source', finish_source)
        obj.set_setting('sportident_start_source', start_source)

        obj.set_setting('sportident_start_cp_number', self.item_start_cp_value.value())
        obj.set_setting('sportident_finish_cp_number', self.item_finish_cp_value.value())

        obj.set_setting('sportident_assign_chip_reading', assign_chip_reading)
        obj.set_setting('sportident_repeated_reading', repeated_reading)

        obj.set_setting('sportident_assignment_mode', self.assignment_mode.isChecked())

        Config.set('autoconnect', self.auto_connect.isChecked())

        if changed:
            win = self.get_main_window()

    def get_main_window(self):
        return GlobalAccess().get_main_window()
