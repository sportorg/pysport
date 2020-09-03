import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QRadioButton,
    QTimeEdit,
)

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.start.start_preparation import change_start_time
from sportorg.utils.time import time_to_otime


class StartTimeChangeDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.time_format = 'hh:mm:ss'

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate('Start time change'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.layout = QFormLayout(self)

        self.time_add = QRadioButton(translate('Add'))
        self.time_add.setChecked(True)
        self.time_reduce = QRadioButton(translate('Reduce'))
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
        self.button_ok.setText(translate('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def apply_changes_impl(self):
        change_start_time(
            self.time_add.isChecked(), time_to_otime(self.time_value.time())
        )
