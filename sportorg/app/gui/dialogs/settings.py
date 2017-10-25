import logging
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QDialog, QCheckBox, QPushButton

from sportorg.language import _
from sportorg import config

from sportorg.app.models.memory import Config


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle(_('Settings'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        # self.setMinimumWidth(540)
        # self.setMinimumHeight(250)
        self.layout = QFormLayout(self)

        self.auto_save = QCheckBox(_('Auto save'))
        self.auto_save.setChecked(Config.get('autosave'))
        self.layout.addRow(self.auto_save)

        self.auto_connect = QCheckBox(_('Auto connect to station'))
        self.auto_connect.setChecked(Config.get('autoconnect'))
        self.layout.addRow(self.auto_connect)

        self.open_recent_file = QCheckBox(_('Open recent file'))
        self.open_recent_file.setChecked(Config.get('open_recent_file'))
        self.layout.addRow(self.open_recent_file)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(e)
            self.close()

        self.button_ok = QPushButton(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

        self.show()

    def apply_changes_impl(self):
        Config.set('autosave', self.auto_save.isChecked())
        Config.set('autoconnect', self.auto_connect.isChecked())
        Config.set('open_recent_file', self.open_recent_file.isChecked())
