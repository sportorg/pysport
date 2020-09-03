import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QSpinBox

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.start.start_preparation import clone_relay_legs


class RelayCloneDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

        self.setWindowTitle(translate('Clone relay legs'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.layout = QFormLayout(self)

        self.min_bib = QSpinBox()
        self.min_bib.setMaximum(10000000)
        self.min_bib.setValue(1001)
        self.layout.addRow(QLabel(translate('Minimal bib')), self.min_bib)

        self.max_bib = QSpinBox()
        self.max_bib.setMaximum(10000000)
        self.max_bib.setValue(2999)
        self.layout.addRow(QLabel(translate('Maximal bib')), self.max_bib)

        self.increment = QSpinBox()
        self.increment.setMaximum(10000000)
        self.increment.setValue(2000)
        self.layout.addRow(QLabel(translate('Increment')), self.increment)

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

        self.show()

    def apply_changes_impl(self):
        min_bib = self.min_bib.value()
        max_bib = self.max_bib.value()
        increment = self.increment.value()
        clone_relay_legs(min_bib, max_bib, increment)
