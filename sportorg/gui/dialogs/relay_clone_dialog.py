import logging

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel
except ModuleNotFoundError:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvSpinBox
from sportorg.language import translate
from sportorg.models.start.start_preparation import clone_relay_legs


class RelayCloneDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

        self.setWindowTitle(translate("Clone relay legs"))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.layout = QFormLayout(self)

        self.min_bib = AdvSpinBox(maximum=10000000, value=1001)
        self.layout.addRow(QLabel(translate("Minimal bib")), self.min_bib)

        self.max_bib = AdvSpinBox(maximum=10000000, value=2999)
        self.layout.addRow(QLabel(translate("Maximal bib")), self.max_bib)

        self.increment = AdvSpinBox(maximum=10000000, value=2000)
        self.layout.addRow(QLabel(translate("Increment")), self.increment)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(e)
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(translate("OK"))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate("Cancel"))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def apply_changes_impl(self):
        min_bib = self.min_bib.value()
        max_bib = self.max_bib.value()
        increment = self.increment.value()
        clone_relay_legs(min_bib, max_bib, increment)
