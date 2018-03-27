import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QDialog, QCheckBox, QDialogButtonBox, QLabel

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _, get_languages
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

        self.label_lang = QLabel(_('Languages'))
        self.item_lang = AdvComboBox()
        self.item_lang.addItems(get_languages())
        self.item_lang.setCurrentText(Config().configuration.get('current_locale', 'ru_RU'))
        self.layout.addRow(self.label_lang, self.item_lang)

        self.item_show_toolbar = QCheckBox(_('Show toolbar'))
        self.item_show_toolbar.setChecked(Config().configuration.get('show_toolbar'))
        self.layout.addRow(self.item_show_toolbar)

        self.item_auto_save = QCheckBox(_('Auto save'))
        self.item_auto_save.setChecked(Config().configuration.get('autosave'))
        self.layout.addRow(self.item_auto_save)

        self.item_auto_connect = QCheckBox(_('Auto connect to station'))
        self.item_auto_connect.setChecked(Config().configuration.get('autoconnect'))
        self.layout.addRow(self.item_auto_connect)

        self.item_open_recent_file = QCheckBox(_('Open recent file'))
        self.item_open_recent_file.setChecked(Config().configuration.get('open_recent_file'))
        self.layout.addRow(self.item_open_recent_file)

        self.item_use_birthday = QCheckBox(_('Use birthday'))
        self.item_use_birthday.setChecked(Config().configuration.get('use_birthday', False))
        self.layout.addRow(self.item_use_birthday)

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
        Config().configuration.set('current_locale', self.item_lang.currentText())
        Config().configuration.set('show_toolbar', self.item_show_toolbar.isChecked())
        Config().configuration.set('autosave', self.item_auto_save.isChecked())
        Config().configuration.set('autoconnect', self.item_auto_connect.isChecked())
        Config().configuration.set('open_recent_file', self.item_open_recent_file.isChecked())
        Config().configuration.set('use_birthday', self.item_use_birthday.isChecked())
        Config().save()
