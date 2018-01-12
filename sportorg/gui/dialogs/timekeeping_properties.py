import logging

from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import QFormLayout, QLabel, QDialog, \
     QTimeEdit, QSpinBox, QRadioButton, QCheckBox, QDialogButtonBox, QWidget, QTabWidget, \
     QGroupBox

from sportorg.core.otime import OTime
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.memory import race, SystemType
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.modules.configs.configs import Config
from sportorg.utils.time import time_to_otime


class TimekeepingPropertiesDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

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
        # self.tk_layout.addRow(self.chip_reading_box)

        self.repeated_reading_box = QGroupBox(_('Repeated reading'))
        self.repeated_reading_layout = QFormLayout()
        self.repeated_reading_rewrite = QRadioButton(_('Rewrite'))
        self.repeated_reading_layout.addRow(self.repeated_reading_rewrite)
        self.repeated_reading_add = QRadioButton(_('Add'))
        self.repeated_reading_layout.addRow(self.repeated_reading_add)
        self.repeated_reading_keep_all_version = QRadioButton(_('Keep all versions'))
        self.repeated_reading_layout.addRow(self.repeated_reading_keep_all_version)
        self.repeated_reading_box.setLayout(self.repeated_reading_layout)
        # self.tk_layout.addRow(self.repeated_reading_box)

        self.assignment_mode = QCheckBox(_('Assignment mode'))
        # self.assignment_mode.stateChanged.connect(self.on_assignment_mode)
        # self.layout.addRow(self.assignment_mode)

        self.auto_connect = QCheckBox(_('Auto connect to station'))
        self.tk_layout.addRow(self.auto_connect)

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
        self.mr_time_edit.setDisplayFormat('hh:mm:ss')
        self.mr_layout.addRow(self.mr_time_radio, self.mr_time_edit)
        self.mr_laps_radio = QRadioButton(_('penalty laps'))
        self.mr_layout.addRow(self.mr_laps_radio)
        self.mr_counting_lap_check = QCheckBox(_('counting lap'))
        self.mr_layout.addRow(self.mr_counting_lap_check)
        self.mr_lap_station_check = QCheckBox(_('lap station'))
        self.mr_lap_station_edit = QSpinBox()
        self.mr_lap_station_edit.setMaximumWidth(50)
        self.mr_layout.addRow(self.mr_lap_station_check, self.mr_lap_station_edit)
        self.marked_route_tab.setLayout(self.mr_layout)

        # team results
        """
        рассчет командных результатов
           количество участников [ Edit ]
           рассчет
             [ x ] по коллективам
             [   ] по субъектам
           сумма
             [ x ] очков
             [   ] времени
             [   ] мест
        """
        self.team_result_tab = QWidget()
        self.team_layout = QFormLayout()
        self.team_qty_label = QLabel(_('Persons in team'))
        self.team_qty_edit = QSpinBox()
        self.team_qty_edit.setMaximumWidth(50)
        self.team_layout.addRow(self.team_qty_label, self.team_qty_edit)

        self.team_group = QGroupBox()
        self.team_group.setTitle(_('Grouping'))
        self.team_group_organization = QRadioButton(_('organization grouping'))
        self.team_group_region = QRadioButton(_('region grouping'))
        self.team_group_layout = QFormLayout()
        self.team_group_layout.addRow(self.team_group_organization)
        self.team_group_layout.addRow(self.team_group_region)
        self.team_group.setLayout(self.team_group_layout)
        self.team_layout.addRow(self.team_group)

        self.team_sum = QGroupBox()
        self.team_sum.setTitle(_('Sum'))
        self.team_sum_scores = QRadioButton(_('scores'))
        self.team_sum_time = QRadioButton(_('time'))
        self.team_sum_places = QRadioButton(_('places'))
        self.team_sum_layout = QFormLayout()
        self.team_sum_layout.addRow(self.team_sum_scores)
        self.team_sum_layout.addRow(self.team_sum_time)
        self.team_sum_layout.addRow(self.team_sum_places)
        self.team_sum.setLayout(self.team_sum_layout)
        self.team_layout.addRow(self.team_sum)

        self.team_result_tab.setLayout(self.team_layout)


        self.tab_widget.addTab(self.timekeeping_tab, _('SPORTident settings'))
        self.tab_widget.addTab(self.result_proc_tab, _('Result processing'))
        self.tab_widget.addTab(self.team_result_tab, _('Team results'))
        self.tab_widget.addTab(self.marked_route_tab, _('Penalty calculation'))

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(str(e))
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
        self.repeated_reading_box.setDisabled(mode)

    def set_values_from_model(self):
        cur_race = race()
        zero_time = cur_race.get_setting('sportident_zero_time', (8, 0, 0))
        start_source = cur_race.get_setting('sportident_start_source', 'protocol')
        start_cp_number = cur_race.get_setting('sportident_start_cp_number', 31)
        finish_source = cur_race.get_setting('sportident_finish_source', 'station')
        finish_cp_number = cur_race.get_setting('sportident_finish_cp_number', 90)
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

        if repeated_reading == 'rewrite':
            self.repeated_reading_rewrite.setChecked(True)
        elif repeated_reading == 'add':
            self.repeated_reading_add.setChecked(True)
        elif repeated_reading == 'keep_all_versions':
            self.repeated_reading_keep_all_version.setChecked(True)

        self.assignment_mode.setChecked(assignment_mode)
        self.auto_connect.setChecked(Config().configuration.get('autoconnect'))

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
        mr_penalty_time = obj.get_setting('marked_route_penalty_time', OTime(sec=60))
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

        # team results
        team_group_mode = obj.get_setting('team_group_mode', 'organization')
        team_sum_mode = obj.get_setting('team_sum_mode', 'scores')
        team_qty = obj.get_setting('team_qty', 4)

        if team_group_mode == 'organization':
            self.team_group_organization.setChecked(True)
        else:
            self.team_group_region.setChecked(True)

        if team_sum_mode == 'scores':
            self.team_sum_scores.setChecked(True)
        elif team_sum_mode == 'time':
            self.team_sum_time.setChecked(True)
        else:
            self.team_sum_places.setChecked(True)

        self.team_qty_edit.setValue(team_qty)

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

        start_cp_number = self.item_start_cp_value.value()
        finish_cp_number = self.item_finish_cp_value.value()

        old_start_source = obj.get_setting('sportident_start_source', 'protocol')
        old_start_cp_number = obj.get_setting('sportident_start_cp_number', 31)
        old_finish_source = obj.get_setting('sportident_finish_source', 'station')
        old_finish_cp_number = obj.get_setting('sportident_finish_cp_number', 90)

        if old_start_source != start_source or old_finish_source != finish_source:
            changed = True
        if old_start_cp_number != start_cp_number or old_finish_cp_number != finish_cp_number:
            changed = True
            for result in race().results:
                if result.system_type == SystemType.SPORTIDENT:
                    result.clear()

        obj.set_setting('sportident_start_source', start_source)
        obj.set_setting('sportident_finish_source', finish_source)

        obj.set_setting('sportident_start_cp_number', start_cp_number)
        obj.set_setting('sportident_finish_cp_number', finish_cp_number)

        obj.set_setting('sportident_assign_chip_reading', assign_chip_reading)
        obj.set_setting('sportident_repeated_reading', repeated_reading)

        obj.set_setting('sportident_assignment_mode', self.assignment_mode.isChecked())

        Config().configuration.set('autoconnect', self.auto_connect.isChecked())

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
        mr_penalty_time = time_to_otime(self.mr_time_edit.time())
        mr_if_counting_lap = self.mr_counting_lap_check.isChecked()
        mr_if_station_check = self.mr_lap_station_check.isChecked()
        mr_station_code = self.mr_lap_station_edit.value()

        obj.set_setting('marked_route_mode', mr_mode)
        obj.set_setting('marked_route_penalty_time', mr_penalty_time)
        obj.set_setting('marked_route_if_counting_lap', mr_if_counting_lap)
        obj.set_setting('marked_route_if_station_check', mr_if_station_check)
        obj.set_setting('marked_route_station_code', mr_station_code)

        # team result


        changed = True

        if changed:
            ResultCalculation().process_results()
            GlobalAccess().get_main_window().refresh()
