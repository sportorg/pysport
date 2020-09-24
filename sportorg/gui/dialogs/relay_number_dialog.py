import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QSpinBox

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.start.relay import (
    get_next_relay_number_protocol,
    set_next_relay_number,
)


class RelayNumberDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate('Relay number'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.layout = QFormLayout(self)

        self.number_label = QLabel(translate('First relay number'))
        self.number_item = QSpinBox()
        self.number_item.setMinimum(1001)
        self.number_item.setMaximum(9999)

        next_number = get_next_relay_number_protocol()
        self.number_item.setValue(next_number)

        self.layout.addRow(self.number_label, self.number_item)

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
        set_next_relay_number(self.number_item.value())
