import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QDialog, QDialogButtonBox, QRadioButton, QTimeEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.start.start_preparation import change_start_time
from sportorg.utils.time import time_to_otime


class StartTimeChangeDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.time_format = 'hh:mm:ss'

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Start time change'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.layout = QFormLayout(self)

        self.time_add = QRadioButton(_('Add'))
        self.time_add.setChecked(True)
        self.time_reduce = QRadioButton(_('Reduce'))
        self.time_value = QTimeEdit()
        self.time_value.setDisplayFormat(self.time_format)

        self.layout.addRow(self.time_add)
        self.layout.addRow(self.time_reduce)
        self.layout.addRow(self.time_value)

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

    def apply_changes_impl(self):
        change_start_time(self.time_add.isChecked(), time_to_otime(self.time_value.time()))
        GlobalAccess().get_main_window().refresh()
