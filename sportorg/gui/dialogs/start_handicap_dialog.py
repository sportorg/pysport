import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QRadioButton,
    QTimeEdit,
)

from sportorg import config
from sportorg.common.otime import OTime
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.memory import race
from sportorg.models.start.start_preparation import (
    handicap_start_time,
    reverse_start_time,
)
from sportorg.utils.time import time_to_otime


class StartHandicapDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.time_format = 'hh:mm:ss'

        self.setWindowTitle(translate('Handicap start time'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.layout = QFormLayout(self)

        self.handicap_mode = QRadioButton(translate('Handicap mode'))
        self.reverse_mode = QRadioButton(translate('Reverse mode'))
        self.layout.addRow(self.handicap_mode)
        self.layout.addRow(self.reverse_mode)

        self.zero_time_label = QLabel(translate('Start time'))
        self.zero_time = QTimeEdit()
        self.zero_time.setDisplayFormat(self.time_format)
        self.layout.addRow(self.zero_time_label, self.zero_time)

        self.max_gap_label = QLabel(translate('Max gap from leader'))
        self.max_gap = QTimeEdit()
        self.max_gap.setDisplayFormat(self.time_format)
        self.layout.addRow(self.max_gap_label, self.max_gap)

        self.second_start_time_label = QLabel(translate('Start time for 2 group'))
        self.second_time = QTimeEdit()
        self.second_time.setDisplayFormat(self.time_format)
        self.layout.addRow(self.second_start_time_label, self.second_time)

        self.interval_time_label = QLabel(translate('Start interval'))
        self.interval_time = QTimeEdit()
        self.interval_time.setDisplayFormat(self.time_format)
        self.layout.addRow(self.interval_time_label, self.interval_time)

        self.dsq_offset_label = QLabel(translate('Offset after DSQ'))
        self.dsq_offset = QTimeEdit()
        self.dsq_offset.setDisplayFormat(self.time_format)
        self.layout.addRow(self.dsq_offset_label, self.dsq_offset)

        def mode_changed():
            status = self.handicap_mode.isChecked()
            self.max_gap.setEnabled(status)
            self.second_time.setEnabled(status)
            self.dsq_offset.setDisabled(status)

        self.handicap_mode.toggled.connect(mode_changed)
        self.reverse_mode.toggled.connect(mode_changed)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.error(str(e))
                logging.exception(e)
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(translate('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.set_values()
        self.show()

    def set_values(self):
        obj = race()
        if obj.get_setting('handicap_mode', True):
            self.handicap_mode.toggle()
        else:
            self.reverse_mode.toggle()
        self.zero_time.setTime(
            OTime(
                msec=obj.get_setting('handicap_start', OTime(0, 11).to_msec())
            ).to_time()
        )
        self.max_gap.setTime(
            OTime(
                msec=obj.get_setting('handicap_max_gap', OTime(0, 0, 30).to_msec())
            ).to_time()
        )
        self.second_time.setTime(
            OTime(
                msec=obj.get_setting(
                    'handicap_second_start', OTime(0, 11, 30).to_msec()
                )
            ).to_time()
        )
        self.interval_time.setTime(
            OTime(
                msec=obj.get_setting('handicap_interval', OTime(0, 0, 1).to_msec())
            ).to_time()
        )
        self.dsq_offset.setTime(
            OTime(
                msec=obj.get_setting('handicap_dsq_offset', OTime(0, 0, 10).to_msec())
            ).to_time()
        )

    def apply_changes_impl(self):
        obj = race()
        obj.set_setting('handicap_mode', self.handicap_mode.isChecked())
        obj.set_setting(
            'handicap_start', time_to_otime(self.zero_time.time()).to_msec()
        )
        obj.set_setting(
            'handicap_max_gap', time_to_otime(self.max_gap.time()).to_msec()
        )
        obj.set_setting(
            'handicap_second_start', time_to_otime(self.second_time.time()).to_msec()
        )
        obj.set_setting(
            'handicap_interval', time_to_otime(self.interval_time.time()).to_msec()
        )
        obj.set_setting(
            'handicap_dsq_offset', time_to_otime(self.dsq_offset.time()).to_msec()
        )

        if obj.get_setting('handicap_mode', True):
            handicap_start_time()
        else:
            reverse_start_time()
