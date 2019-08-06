import logging
import re

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QFormLayout, QLabel, QDialog, QDialogButtonBox, QLineEdit, QCheckBox, QTextEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.memory import race


class LiveDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.url_regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def exec_(self):
        self.init_ui()
        self.set_values()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_('Live'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_url = QLabel(_('URL'))
        self.item_url = QLineEdit()
        self.item_url.textChanged.connect(self.url_validation)
        self.layout.addRow(self.label_url, self.item_url)

        self.label_token = QLabel(_('Token'))
        self.item_token = QLineEdit()
        # self.layout.addRow(self.label_token, self.item_token)

        self.label_valid_url = QLabel('')
        self.layout.addRow(QLabel(''), self.label_valid_url)

        self.item_live_enabled = QCheckBox(_('Enabled'))
        self.layout.addRow(self.item_live_enabled)

        self.hint = QTextEdit(_('Ctrl+K - send selected'))
        self.hint.append(_('Ctrl+K on groups - send start list'))
        self.hint.setDisabled(True)
        self.hint.setMaximumHeight(70)
        self.layout.addRow(self.hint)

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

    def url_validation(self):
        url = self.item_url.text()
        self.label_valid_url.setText('')
        if url:
            valid = self.url_regex.match(url)
            if not valid:
                self.label_valid_url.setText(_('URL not valid'))

    def set_values(self):
        obj = race()
        url = obj.get_setting('live_url', '')
        token = obj.get_setting('live_token', '')
        live_enabled = obj.get_setting('live_enabled', False)

        self.item_url.setText(url)
        self.item_token.setText(token)
        self.item_live_enabled.setChecked(live_enabled)

    def apply_changes_impl(self):
        obj = race()
        obj.set_setting('live_url', self.item_url.text())
        obj.set_setting('live_token', self.item_token.text())
        obj.set_setting('live_enabled', self.item_live_enabled.isChecked())
        logging.debug('Saving settings of live')
