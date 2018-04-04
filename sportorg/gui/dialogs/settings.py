import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QDialog, QCheckBox, QDialogButtonBox, QLabel, QTabWidget, QWidget

from sportorg import config
from sportorg.core.audio import get_sounds
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _, get_languages
from sportorg.modules.configs.configs import Config
from sportorg.modules.sound import Sound


class Tab:
    def save(self):
        pass


class MainTab(Tab):
    def __init__(self, parent):
        self.widget = QWidget()
        self.layout = QFormLayout(parent)

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

        self.item_auto_connect = QCheckBox(_('Auto connect to SPORTident station'))
        self.item_auto_connect.setChecked(Config().configuration.get('autoconnect'))
        self.layout.addRow(self.item_auto_connect)

        self.item_open_recent_file = QCheckBox(_('Open recent file'))
        self.item_open_recent_file.setChecked(Config().configuration.get('open_recent_file'))
        self.layout.addRow(self.item_open_recent_file)

        self.item_use_birthday = QCheckBox(_('Use birthday'))
        self.item_use_birthday.setChecked(Config().configuration.get('use_birthday'))
        self.layout.addRow(self.item_use_birthday)

        self.widget.setLayout(self.layout)

    def save(self):
        Config().configuration.set('current_locale', self.item_lang.currentText())
        Config().configuration.set('show_toolbar', self.item_show_toolbar.isChecked())
        Config().configuration.set('autosave', self.item_auto_save.isChecked())
        Config().configuration.set('autoconnect', self.item_auto_connect.isChecked())
        Config().configuration.set('open_recent_file', self.item_open_recent_file.isChecked())
        Config().configuration.set('use_birthday', self.item_use_birthday.isChecked())


class SoundTab(Tab):
    def __init__(self, parent):
        self.widget = QWidget()
        self.layout = QFormLayout(parent)

        self.sounds = get_sounds()

        self.item_enabled = QCheckBox(_('Enabled'))
        self.item_enabled.setChecked(Config().sound.get('enabled'))
        self.layout.addRow(self.item_enabled)

        self.label_successful = QLabel(_('Successful result'))
        self.item_successful = AdvComboBox()
        self.item_successful.addItems(self.sounds)
        self.item_successful.setCurrentText(Config().sound.get('successful') or config.sound_dir('ok.wav'))
        self.layout.addRow(self.label_successful, self.item_successful)

        self.label_unsuccessful = QLabel(_('Unsuccessful result'))
        self.item_unsuccessful = AdvComboBox()
        self.item_unsuccessful.addItems(self.sounds)
        self.item_unsuccessful.setCurrentText(Config().sound.get('unsuccessful') or config.sound_dir('failure.wav'))
        self.layout.addRow(self.label_unsuccessful, self.item_unsuccessful)

        self.widget.setLayout(self.layout)

    def save(self):
        Config().sound.set('enabled', self.item_enabled.isChecked())
        Config().sound.set('successful', self.item_successful.currentText())
        Config().sound.set('unsuccessful', self.item_unsuccessful.currentText())


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.widgets = [
            (MainTab(self), _('Main settings')),
            (SoundTab(self), _('Sounds')),
        ]

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Settings'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.tab_widget = QTabWidget()

        for tab, title in self.widgets:
            self.tab_widget.addTab(tab.widget, title)

        self.layout = QFormLayout(self)
        self.layout.addRow(self.tab_widget)

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
        for tab, _ in self.widgets:
            tab.save()
        Config().save()
