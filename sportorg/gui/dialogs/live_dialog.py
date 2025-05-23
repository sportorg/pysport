import logging
import re
from typing import List

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QLabel,
        QLineEdit,
        QTextEdit,
    )
except ModuleNotFoundError:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import (
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QLabel,
        QLineEdit,
        QTextEdit,
    )

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvSpinBox
from sportorg.language import translate
from sportorg.models.memory import race


class LiveDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.url_regex = re.compile(
            r"^(?:http|ftp)s?://"  # http:// or https://
            r"(?:(?:[A-Z\d](?:[A-Z\d-]{0,61}[A-Z\d])?\.)+(?:[A-Z]{2,6}\.?|[A-Z\d-]{2,}\.?)|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

    def exec_(self):
        self.init_ui()
        self.set_values()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate("Live"))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_url = QLabel(translate("URL"))
        self.item_url = QLineEdit()
        self.item_url.textChanged.connect(self.url_validation)
        self.layout.addRow(self.label_url, self.item_url)

        self.label_valid_url = QLabel("")
        self.layout.addRow(QLabel(""), self.label_valid_url)

        self.item_live_enabled = QCheckBox(translate("Enabled"))
        self.layout.addRow(self.item_live_enabled)

        self.item_sending_all_controls = QCheckBox(
            translate("Sending the entire contents of the chip")
        )
        self.item_sending_all_controls.setChecked(True)
        self.layout.addRow(self.item_sending_all_controls)

        self.item_result_sending = QCheckBox(translate("Online results sending"))
        self.item_result_sending.setChecked(True)
        self.layout.addRow(self.item_result_sending)

        self.item_cp_sending = QCheckBox(translate("Online CP sending"))
        self.item_result_sending.setChecked(True)
        self.layout.addRow(self.item_cp_sending)
        self.item_cp_sending.setChecked(False)

        self.online_cp_box = QGroupBox(translate("Online CP settings"))
        self.online_cp_layout = QFormLayout()

        self.online_cp_from_splits = QCheckBox(translate("CP from splits"))
        self.online_cp_from_splits.setChecked(True)
        self.online_cp_from_splits_codes = QLineEdit("90,91,92")
        self.online_cp_from_splits_codes.setMaximumWidth(120)
        self.online_cp_layout.addRow(
            self.online_cp_from_splits, self.online_cp_from_splits_codes
        )

        self.online_cp_from_finish = QCheckBox(translate("Finish as CP"))
        self.online_cp_from_finish.setChecked(True)
        self.online_cp_from_finish_code = AdvSpinBox(
            minimum=0, maximum=1024, value=80, max_width=60
        )
        self.online_cp_layout.addRow(
            self.online_cp_from_finish, self.online_cp_from_finish_code
        )

        self.online_cp_box.setLayout(self.online_cp_layout)
        self.layout.addRow(self.online_cp_box)

        self.hint = QTextEdit(translate("Ctrl+K - send selected"))
        self.hint.append(translate("Ctrl+K on groups - send start list"))
        self.hint.setDisabled(True)
        self.hint.setMaximumHeight(70)
        self.layout.addRow(self.hint)

        self.item_live_enabled.stateChanged.connect(
            self.on_enable_checkbox_state_changed
        )
        self.item_cp_sending.stateChanged.connect(self.on_cp_sending_state_changed)

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
        self.button_ok.setText(translate("OK"))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate("Cancel"))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def on_cp_sending_state_changed(self):
        state = self.item_cp_sending.isChecked()
        self.online_cp_box.setEnabled(state)

    def on_enable_checkbox_state_changed(self):
        state = self.item_live_enabled.isChecked()
        self.item_sending_all_controls.setEnabled(state)
        self.item_result_sending.setEnabled(state)
        self.item_cp_sending.setEnabled(state)
        self.online_cp_box.setEnabled(state)

        if state:
            self.on_cp_sending_state_changed()

    def url_validation(self):
        urls = decode_urls(self.item_url.text())
        self.label_valid_url.setText("")
        for url in urls:
            if not self.url_regex.match(url):
                self.label_valid_url.setText(translate("URL not valid"))
                return

    def set_values(self):
        obj = race()
        url = obj.get_setting("live_url", "")  # save compatibility
        urls = obj.get_setting("live_urls", [])
        if not urls:
            urls = [url]
        live_enabled = obj.get_setting("live_enabled", False)

        live_sending_all_controls = obj.get_setting("live_sending_all_controls", False)
        live_results_enabled = obj.get_setting("live_results_enabled", True)
        live_cp_enabled = obj.get_setting("live_cp_enabled", False)
        live_cp_code = obj.get_setting("live_cp_code", "10")
        live_cp_split_codes = obj.get_setting("live_cp_split_codes", "91,91,92")
        live_cp_finish_enabled = obj.get_setting("live_cp_finish_enabled", True)
        live_cp_splits_enabled = obj.get_setting("live_cp_splits_enabled", True)

        self.item_url.setText(encode_urls(urls))
        self.item_live_enabled.setChecked(live_enabled)
        self.item_sending_all_controls.setChecked(live_sending_all_controls)
        self.item_result_sending.setChecked(live_results_enabled)
        self.item_cp_sending.setChecked(live_cp_enabled)
        self.online_cp_from_finish_code.setValue(int(live_cp_code))
        self.online_cp_from_splits_codes.setText(live_cp_split_codes)
        self.online_cp_from_finish.setChecked(live_cp_finish_enabled)
        self.online_cp_from_splits.setChecked(live_cp_splits_enabled)

        self.on_enable_checkbox_state_changed()

    def apply_changes_impl(self):
        obj = race()
        obj.set_setting("live_urls", decode_urls(self.item_url.text()))
        obj.set_setting("live_enabled", self.item_live_enabled.isChecked())
        obj.set_setting(
            "live_sending_all_controls", self.item_sending_all_controls.isChecked()
        )
        obj.set_setting("live_results_enabled", self.item_result_sending.isChecked())
        obj.set_setting("live_cp_enabled", self.item_cp_sending.isChecked())
        obj.set_setting(
            "live_cp_finish_enabled", self.online_cp_from_finish.isChecked()
        )
        obj.set_setting("live_cp_code", self.online_cp_from_finish_code.text())
        obj.set_setting(
            "live_cp_splits_enabled", self.online_cp_from_splits.isChecked()
        )
        obj.set_setting("live_cp_split_codes", self.online_cp_from_splits_codes.text())

        logging.debug("Saving settings of live")


def decode_urls(url: str) -> List[str]:
    urls = url.split("|")
    return [url.strip() for url in urls]


def encode_urls(urls: List[str]) -> str:
    return "|".join(urls)
