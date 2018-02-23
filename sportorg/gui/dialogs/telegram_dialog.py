import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QDialog, QDialogButtonBox, QLineEdit, QCheckBox, QGroupBox, \
    QRadioButton, QTextEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.memory import race


class TelegramDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec(self):
        self.init_ui()
        self.set_values()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Telegram'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_token = QLabel(_('Token'))
        self.item_token = QLineEdit()
        self.layout.addRow(self.label_token, self.item_token)

        self.label_chat_id = QLabel(_('Chat id'))
        self.item_chat_id = QLineEdit()
        self.layout.addRow(self.label_chat_id, self.item_chat_id)

        self.label_template = QLabel(_('Template'))
        self.item_template = QTextEdit()
        self.item_template.setMinimumHeight(150)
        self.layout.addRow(self.label_template, self.item_template)

        self.item_enabled = QCheckBox(_('Enabled'))
        self.layout.addRow(self.item_enabled)

        self.parse_mode_groupbox = QGroupBox()
        self.parse_mode_groupbox.setTitle(_('Parse mode'))
        self.parse_mode_groupbox_layout = QFormLayout()
        self.parse_mode_item_text = QRadioButton(_('Text'))
        self.parse_mode_item_markdown = QRadioButton(_('Markdown'))
        self.parse_mode_item_html = QRadioButton(_('HTML'))
        self.parse_mode_groupbox_layout.addRow(self.parse_mode_item_text)
        self.parse_mode_groupbox_layout.addRow(self.parse_mode_item_markdown)
        self.parse_mode_groupbox_layout.addRow(self.parse_mode_item_html)
        self.parse_mode_groupbox.setLayout(self.parse_mode_groupbox_layout)
        self.layout.addRow(self.parse_mode_groupbox)

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

    def set_values(self):
        obj = race()
        token = obj.get_setting('telegram_token', '')
        url = obj.get_setting('telegram_chat_id', '')
        parse_mode = obj.get_setting('telegram_parse_mode', '')
        template = obj.get_setting('telegram_template', '{group} {name} {bib} {result} {place}')
        telegram_enabled = obj.get_setting('telegram_enabled', False)

        self.item_chat_id.setText(url)
        self.item_token.setText(token)
        self.item_template.setText(template)
        self.item_enabled.setChecked(telegram_enabled)

        if parse_mode == '':
            self.parse_mode_item_text.setChecked(True)
        elif parse_mode == 'Markdown':
            self.parse_mode_item_markdown.setChecked(True)
        elif parse_mode == 'HTML':
            self.parse_mode_item_html.setChecked(True)

    def apply_changes_impl(self):
        parse_mode = ''
        if self.parse_mode_item_markdown.isChecked():
            parse_mode = 'Markdown'
        elif self.parse_mode_item_html.isChecked():
            parse_mode = 'HTML'

        obj = race()
        obj.set_setting('telegram_token', self.item_token.text())
        obj.set_setting('telegram_chat_id', self.item_chat_id.text())
        obj.set_setting('telegram_enabled', self.item_enabled.isChecked())
        obj.set_setting('telegram_parse_mode', parse_mode)
        obj.set_setting('telegram_template', self.item_template.toPlainText())
