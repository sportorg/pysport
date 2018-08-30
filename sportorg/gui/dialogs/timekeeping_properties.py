import logging

from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import QFormLayout, QLabel, QDialog, \
     QTimeEdit, QSpinBox, QRadioButton, QCheckBox, QDialogButtonBox, QWidget, QTabWidget, \
     QGroupBox, QLineEdit

from sportorg.core.otime import OTime
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.memory import race
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.modules.sportident.sireader import SIReaderClient
from sportorg.utils.time import time_to_otime


class TimekeepingPropertiesDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.time_format = 'hh:mm:ss'

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        # self.setFixedWidth(500)
        self.setWindowTitle(_('Timekeeping settings'))
        # self.setWindowIcon(QIcon(icon_dir('sportident.png')))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.tab_widget = QTabWidget()

        # timekeeping tab
        self.timekeeping_tab = QWidget()
        self.tk_layout = QFormLayout()

        self.label_zero_time = QLabel(_('Zero time'))
        self.item_zero_time = QTimeEdit()
        self.item_zero_time.setDisplayFormat("HH:mm")
        self.item_zero_time.setMaximumSize(60, 20)
        self.item_zero_time.setDisabled(True)
        self.tk_layout.addRow(self.label_zero_time, self.item_zero_time)

        self.label_si_port = QLabel(_('Available Ports'))
        self.item_si_port = AdvComboBox()
        self.item_si_port.addItems(SIReaderClient().get_ports())
        self.tk_layout.addRow(self.label_si_port, self.item_si_port)

        self.start_group_box = QGroupBox(_('Start time'))
        self.start_layout = QFormLayout()
        self.item_start_protocol = QRadioButton(_('From protocol'))
        self.start_layout.addRow(self.item_start_protocol)
        self.item_start_station = QRadioButton(_('Start station'))
        self.start_layout.addRow(self.item_start_station)
        self.item_start_cp = QRadioButton(_('Control point'))
        self.item_start_cp_value = QSpinBox()
        self.item_start_cp_value.setMaximumSize(60, 20)
        self.start_layout.addRow(self.item_start_cp, self.item_start_cp_value)
        self.item_start_gate = QRadioButton(_('Start gate'))
        self.item_start_gate.setDisabled(True)
        self.start_layout.addRow(self.item_start_gate)
        self.start_group_box.setLayout(self.start_layout)
        self.tk_layout.addRow(self.start_group_box)

        self.finish_group_box = QGroupBox(_('Finish time'))
        self.finish_layout = QFormLayout()
        self.item_finish_station = QRadioButton(_('Finish station'))
        self.finish_layout.addRow(self.item_finish_station)
        self.item_finish_cp = QRadioButton(_('Control point'))
        self.item_finish_cp_value = QSpinBox()
        self.item_finish_cp_value.setMinimum(-1)
        self.item_finish_cp_value.setMaximumSize(60, 20)
        self.finish_layout.addRow(self.item_finish_cp, self.item_finish_cp_value)
        self.item_finish_beam = QRadioButton(_('Light beam'))
        self.item_finish_beam.setDisabled(True)
        self.finish_layout.addRow(self.item_finish_beam)
        self.finish_group_box.setLayout(self.finish_layout)
        self.tk_layout.addRow(self.finish_group_box)

        self.chip_reading_box = QGroupBox(_('Assigning a chip when reading'))
        self.chip_reading_layout = QFormLayout()
        self.chip_reading_off = QRadioButton(_('Off'))
        self.chip_reading_layout.addRow(self.chip_reading_off)
        self.chip_reading_unknown = QRadioButton(_('Only unknown members'))
        self.chip_reading_layout.addRow(self.chip_reading_unknown)
        self.chip_reading_always = QRadioButton(_('Always'))
        self.chip_reading_layout.addRow(self.chip_reading_always)
        self.chip_reading_box.setLayout(self.chip_reading_layout)
        self.tk_layout.addRow(self.chip_reading_box)

        self.chip_re_reading = QCheckBox(_('Ask for a bib when re-reading the card'))
        self.chip_reading_layout.addRow(self.chip_re_reading)

        self.assignment_mode = QCheckBox(_('Assignment mode'))
        self.assignment_mode.stateChanged.connect(self.on_assignment_mode)
        self.tk_layout.addRow(self.assignment_mode)

        self.timekeeping_tab.setLayout(self.tk_layout)

        # result processing tab
        self.result_proc_tab = QWidget()
        self.result_proc_layout = QFormLayout()
        self.rp_time_radio = QRadioButton(_('by time'))
        self.result_proc_layout.addRow(self.rp_time_radio)
        self.rp_scores_radio = QRadioButton(_('by scores'))
        self.result_proc_layout.addRow(self.rp_scores_radio)

        self.rp_scores_group = QGroupBox()
        self.rp_scores_layout = QFormLayout(self.rp_scores_group)
        self.rp_rogain_scores_radio = QRadioButton(_('rogain scores'))
        self.rp_scores_layout.addRow(self.rp_rogain_scores_radio)
        self.rp_fixed_scores_radio = QRadioButton(_('fixed scores'))
        self.rp_fixed_scores_edit = QSpinBox()
        self.rp_fixed_scores_edit.setMaximumWidth(50)
        self.rp_scores_layout.addRow(self.rp_fixed_scores_radio, self.rp_fixed_scores_edit)
        self.rp_scores_minute_penalty_label = QLabel(_('minute penalty'))
        self.rp_scores_minute_penalty_edit = QSpinBox()
        self.rp_scores_minute_penalty_edit.setMaximumWidth(50)
        self.rp_scores_layout.addRow(self.rp_scores_minute_penalty_label, self.rp_scores_minute_penalty_edit)
        self.result_proc_layout.addRow(self.rp_scores_group)
        self.result_proc_tab.setLayout(self.result_proc_layout)

        # marked route settings
        self.marked_route_tab = QWidget()
        self.mr_layout = QFormLayout()
        self.mr_off_radio = QRadioButton(_('no penalty'))
        self.mr_layout.addRow(self.mr_off_radio)
        self.mr_time_radio = QRadioButton(_('penalty time'))
        self.mr_time_edit = QTimeEdit()
        self.mr_time_edit.setDisplayFormat(self.time_format)
        self.mr_layout.addRow(self.mr_time_radio, self.mr_time_edit)
        self.mr_laps_radio = QRadioButton(_('penalty laps'))
        self.mr_layout.addRow(self.mr_laps_radio)
        self.mr_counting_lap_check = QCheckBox(_('counting lap'))
        self.mr_counting_lap_check.setDisabled(True)  # TODO
        self.mr_layout.addRow(self.mr_counting_lap_check)
        self.mr_lap_station_check = QCheckBox(_('lap station'))
        self.mr_lap_station_check.setDisabled(True)  # TODO
        self.mr_lap_station_edit = QSpinBox()
        self.mr_lap_station_edit.setMaximumWidth(50)
        self.mr_layout.addRow(self.mr_lap_station_check, self.mr_lap_station_edit)
        self.marked_route_tab.setLayout(self.mr_layout)

        # scores
        """
        Scores
            [ x ] scores array
                40, 37, 35, 33, ... 2, 1 [ Edit ]
            [   ] scores formula
                1000 -  1000 * result / leader [ Edit ]
        """
        self.scores_tab = QWidget()
        self.scores_layout = QFormLayout()
        self.scores_off = QRadioButton(_('scores off'))
        self.scores_array = QRadioButton(_('scores array'))
        self.scores_array_edit = QLineEdit()
        self.scores_formula = QRadioButton(_('scores formula'))
        self.scores_formula_edit = QLineEdit()
        self.scores_formula_hint = QLabel(_('scores formula hint'))
        self.scores_formula_hint.setWordWrap(True)
        self.scores_layout.addRow(self.scores_off)
        self.scores_layout.addRow(self.scores_array)
        self.scores_layout.addRow(self.scores_array_edit)
        self.scores_layout.addRow(self.scores_formula)
        self.scores_layout.addRow(self.scores_formula_edit)
        self.scores_layout.addRow(self.scores_formula_hint)
        self.scores_tab.setLayout(self.scores_layout)

        # time settings
        self.time_settings_tab = QWidget()
        self.time_settings_layout = QFormLayout()
        self.time_settings_accuracy_label = QLabel(_('Accuracy'))
        self.time_settings_accuracy_edit = QSpinBox()
        self.time_settings_accuracy_edit.setMaximumWidth(50)
        self.time_settings_accuracy_edit.setMaximum(3)
        self.time_settings_layout.addRow(self.time_settings_accuracy_label, self.time_settings_accuracy_edit)

        self.time_settings_format = QGroupBox()
        self.time_settings_format.setTitle(_('Format of competitions'))
        self.time_settings_format_less = QRadioButton(_('< 24'))
        self.time_settings_format_more = QRadioButton(_('> 24'))
        self.time_settings_format_layout = QFormLayout()
        self.time_settings_format_layout.addRow(self.time_settings_format_less)
        self.time_settings_format_layout.addRow(self.time_settings_format_more)
        self.time_settings_format.setLayout(self.time_settings_format_layout)
        self.time_settings_layout.addRow(self.time_settings_format)

        self.time_settings_tab.setLayout(self.time_settings_layout)

        self.tab_widget.addTab(self.timekeeping_tab, _('SPORTident (Sportiduino, ...) settings'))
        self.tab_widget.addTab(self.result_proc_tab, _('Result processing'))
        self.tab_widget.addTab(self.scores_tab, _('Scores'))
        self.tab_widget.addTab(self.marked_route_tab, _('Penalty calculation'))
        self.tab_widget.addTab(self.time_settings_tab, _('Time settings'))

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

        self.layout = QFormLayout(self)
        self.layout.addRow(self.tab_widget)
        self.layout.addRow(button_box)

        self.set_values_from_model()

        self.show()

    def on_assignment_mode(self):
        mode = False
        if self.assignment_mode.isChecked():
            mode = True
        self.start_group_box.setDisabled(mode)
        self.finish_group_box.setDisabled(mode)
        self.chip_reading_box.setDisabled(mode)

    def set_values_from_model(self):
        cur_race = race()
        zero_time = cur_race.get_setting('system_zero_time', (8, 0, 0))
        start_source = cur_race.get_setting('system_start_source', 'protocol')
        start_cp_number = cur_race.get_setting('system_start_cp_number', 31)
        finish_source = cur_race.get_setting('system_finish_source', 'station')
        finish_cp_number = cur_race.get_setting('system_finish_cp_number', 90)
        assign_chip_reading = cur_race.get_setting('system_assign_chip_reading', 'off')
        card_read_repeated = cur_race.get_setting('system_card_read_repeated', False)
        assignment_mode = cur_race.get_setting('system_assignment_mode', False)
        si_port = cur_race.get_setting('system_port', '')

        self.item_zero_time.setTime(QTime(zero_time[0], zero_time[1]))

        self.item_si_port.setCurrentText(si_port)

        if start_source == 'protocol':
            self.item_start_protocol.setChecked(True)
        elif start_source == 'station':
            self.item_start_station.setChecked(True)
        elif start_source == 'cp':
            self.item_start_cp.setChecked(True)
        elif start_source == 'gate':
            self.item_start_gate.setChecked(True)

        self.item_start_cp_value.setValue(start_cp_number)

        if finish_source == 'station':
            self.item_finish_station.setChecked(True)
        elif finish_source == 'cp':
            self.item_finish_cp.setChecked(True)
        elif finish_source == 'beam':
            self.item_finish_beam.setChecked(True)

        self.item_finish_cp_value.setValue(finish_cp_number)

        if assign_chip_reading == 'off':
            self.chip_reading_off.setChecked(True)
        elif assign_chip_reading == 'only_unknown_members':
            self.chip_reading_unknown.setChecked(True)
        elif assign_chip_reading == 'always':
            self.chip_reading_always.setChecked(True)

        self.chip_re_reading.setChecked(card_read_repeated)
        self.assignment_mode.setChecked(assignment_mode)

        # result processing
        obj = cur_race
        rp_mode = obj.get_setting('result_processing_mode', 'time')
        rp_score_mode = obj.get_setting('result_processing_score_mode', 'rogain')
        rp_fixed_scores_value = obj.get_setting('result_processing_fixed_score_value', 1)
        rp_scores_minute_penalty = obj.get_setting('result_processing_scores_minute_penalty', 1)

        if rp_mode == 'time':
            self.rp_time_radio.setChecked(True)
        else:
            self.rp_scores_radio.setChecked(True)

        if rp_score_mode == 'rogain':
            self.rp_rogain_scores_radio.setChecked(True)
        else:
            self.rp_fixed_scores_radio.setChecked(True)

        self.rp_fixed_scores_edit.setValue(rp_fixed_scores_value)
        self.rp_scores_minute_penalty_edit.setValue(rp_scores_minute_penalty)

        # penalty calculation

        mr_mode = obj.get_setting('marked_route_mode', 'off')
        mr_penalty_time = OTime(msec=obj.get_setting('marked_route_penalty_time', 60000))
        mr_if_counting_lap = obj.get_setting('marked_route_if_counting_lap', True)
        mr_if_station_check = obj.get_setting('marked_route_if_station_check', False)
        mr_station_code = obj.get_setting('marked_route_station_code', 80)

        if mr_mode == 'off':
            self.mr_off_radio.setChecked(True)
        elif mr_mode == 'time':
            self.mr_time_radio.setChecked(True)
        else:
            self.mr_laps_radio.setChecked(True)

        self.mr_time_edit.setTime(mr_penalty_time.to_time())
        self.mr_counting_lap_check.setChecked(mr_if_counting_lap)
        self.mr_lap_station_check.setChecked(mr_if_station_check)
        self.mr_lap_station_edit.setValue(mr_station_code)

        # score settings

        scores_mode = obj.get_setting('scores_mode', 'off')
        scores_array = obj.get_setting('scores_array', '40,37,35,33,32,31,30,29,28,27,26,25,24,23,22,21,20,19,18,17,'
                                                       '16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1')
        scores_formula = obj.get_setting('scores_formula', '200 - 100 * time / leader')

        if scores_mode == 'off':
            self.scores_off.setChecked(True)
        elif scores_mode == 'array':
            self.scores_array.setChecked(True)
        elif scores_mode == 'formula':
            self.scores_formula.setChecked(True)

        self.scores_array_edit.setText(scores_array)
        self.scores_formula_edit.setText(scores_formula)

        # time settings
        time_accuracy = obj.get_setting('time_accuracy', 0)
        time_format_24 = obj.get_setting('time_format_24', 'less24')

        self.time_settings_accuracy_edit.setValue(time_accuracy)
        if time_format_24 == 'less24':
            self.time_settings_format_less.setChecked(True)
        elif time_format_24 == 'more24':
            self.time_settings_format_more.setChecked(True)

    def apply_changes_impl(self):
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

        start_cp_number = self.item_start_cp_value.value()
        finish_cp_number = self.item_finish_cp_value.value()

        old_start_cp_number = obj.get_setting('system_start_cp_number', 31)
        old_finish_cp_number = obj.get_setting('system_finish_cp_number', 90)

        if old_start_cp_number != start_cp_number or old_finish_cp_number != finish_cp_number:
            race().clear_results()

        obj.set_setting('system_port', self.item_si_port.currentText())

        obj.set_setting('system_start_source', start_source)
        obj.set_setting('system_finish_source', finish_source)

        obj.set_setting('system_start_cp_number', start_cp_number)
        obj.set_setting('system_finish_cp_number', finish_cp_number)

        obj.set_setting('system_assign_chip_reading', assign_chip_reading)

        obj.set_setting('system_card_read_repeated', self.chip_re_reading.isChecked())
        obj.set_setting('system_assignment_mode', self.assignment_mode.isChecked())

        # result processing
        rp_mode = 'time'
        if self.rp_scores_radio.isChecked():
            rp_mode = 'scores'

        rp_score_mode = 'rogain'
        if self.rp_fixed_scores_radio.isChecked():
            rp_score_mode = 'fixed'

        rp_fixed_scores_value = self.rp_fixed_scores_edit.value()

        rp_scores_minute_penalty = self.rp_scores_minute_penalty_edit.value()

        obj.set_setting('result_processing_mode', rp_mode)
        obj.set_setting('result_processing_score_mode', rp_score_mode)
        obj.set_setting('result_processing_fixed_score_value', rp_fixed_scores_value)
        obj.set_setting('result_processing_scores_minute_penalty', rp_scores_minute_penalty)

        # marked route
        mr_mode = 'off'
        if self.mr_laps_radio.isChecked():
            mr_mode = 'laps'
        if self.mr_time_radio.isChecked():
            mr_mode = 'time'

        obj.set_setting('marked_route_mode', mr_mode)
        mr_penalty_time = time_to_otime(self.mr_time_edit.time()).to_msec()
        mr_if_counting_lap = self.mr_counting_lap_check.isChecked()
        mr_if_station_check = self.mr_lap_station_check.isChecked()
        mr_station_code = self.mr_lap_station_edit.value()

        obj.set_setting('marked_route_mode', mr_mode)
        obj.set_setting('marked_route_penalty_time', mr_penalty_time)
        obj.set_setting('marked_route_if_counting_lap', mr_if_counting_lap)
        obj.set_setting('marked_route_if_station_check', mr_if_station_check)
        obj.set_setting('marked_route_station_code', mr_station_code)

        # score settings

        scores_mode = 'off'
        if self.scores_array.isChecked():
            scores_mode = 'array'
        elif self.scores_formula.isChecked():
            scores_mode = 'formula'

        scores_array = self.scores_array_edit.text()
        scores_formula = self.scores_formula_edit.text()

        obj.set_setting('scores_mode', scores_mode)
        obj.set_setting('scores_array', scores_array)
        obj.set_setting('scores_formula', scores_formula)

        # time settings
        time_accuracy = self.time_settings_accuracy_edit.value()
        time_format_24 = 'less24'
        if self.time_settings_format_more.isChecked():
            time_format_24 = 'more24'

        obj.set_setting('time_accuracy', time_accuracy)
        obj.set_setting('time_format_24', time_format_24)

        ResultCalculation(race()).process_results()
        GlobalAccess().get_main_window().refresh()
