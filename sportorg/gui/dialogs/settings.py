import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QDialog, QCheckBox, QPushButton, QDialogButtonBox

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.modules.configs.configs import Config


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Settings'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        # self.setMinimumWidth(540)
        # self.setMinimumHeight(250)
        self.layout = QFormLayout(self)

        self.show_toolbar = QCheckBox(_('Show toolbar'))
        self.show_toolbar.setChecked(Config().configuration.get('show_toolbar'))
        self.layout.addRow(self.show_toolbar)

        self.auto_save = QCheckBox(_('Auto save'))
        self.auto_save.setChecked(Config().configuration.get('autosave'))
        self.layout.addRow(self.auto_save)

        self.auto_connect = QCheckBox(_('Auto connect to station'))
        self.auto_connect.setChecked(Config().configuration.get('autoconnect'))
        self.layout.addRow(self.auto_connect)

        self.open_recent_file = QCheckBox(_('Open recent file'))
        self.open_recent_file.setChecked(Config().configuration.get('open_recent_file'))
        self.layout.addRow(self.open_recent_file)

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
        self.layout.addRow(button_box)

        self.show()

    def apply_changes_impl(self):
        Config().configuration.set('show_toolbar', self.show_toolbar.isChecked())
        Config().configuration.set('autosave', self.auto_save.isChecked())
        Config().configuration.set('autoconnect', self.auto_connect.isChecked())
        Config().configuration.set('open_recent_file', self.open_recent_file.isChecked())
