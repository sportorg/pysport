import logging

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QTextEdit,
        QMessageBox,
    )
except ModuleNotFoundError:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QTextEdit,
        QMessageBox,
    )

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import translate
from sportorg.models.constant import StatusComments
from sportorg.models.memory import ResultManual, ResultStatus, race
from sportorg.models.result.result_tools import recalculate_results
from sportorg.modules.live.live import live_client
from sportorg.modules.teamwork.teamwork import Teamwork


class InputStartNumbersDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.STARTED_NUMBERS = translate("Set started numbers")
        self.NOT_STARTED_NUMBERS = translate("Set not started numbers")

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate("Set DNS numbers"))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.input_start_list = AdvComboBox()
        self.input_start_list.addItems([self.NOT_STARTED_NUMBERS, self.STARTED_NUMBERS])

        self.layout.addRow(self.input_start_list)

        self.item_status_comment = AdvComboBox()
        self.item_status_comment.addItems(StatusComments().get_all())

        self.layout.addRow(
            translate("Label status not started"), self.item_status_comment
        )

        self.label_controls = QLabel("\n\n1 4 15 25\n58 32\n33\n34\n...\n150")
        self.item_numbers = QTextEdit()

        self.layout.addRow(self.label_controls, self.item_numbers)

        def cancel_changes():
            self.person = None
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
        if self.input_start_list.currentText() == self.NOT_STARTED_NUMBERS:
            not_started_numbers = self.parse_input_numbers()
            self.apply_not_started_list_changes_impl(not_started_numbers)
        else:
            self.apply_started_list_changes_impl()

    def apply_started_list_changes_impl(self):
        started_numbers = self.parse_input_numbers()
        all_numbers = set(race().person_index_bib.keys())
        not_started_numbers = set(all_numbers)
        for number in started_numbers:
            if number in not_started_numbers:
                not_started_numbers.remove(number)
            else:
                logging.info("Number %s not found", str(number))

        if len(not_started_numbers) <= len(all_numbers) / 2:
            self.apply_not_started_list_changes_impl(not_started_numbers)
        else:
            QMessageBox.warning(
                self,
                translate("Set started numbers"),
                translate("Count started numbers less half"),
            )

    def apply_not_started_list_changes_impl(self, not_started_numbers):
        status_comment = StatusComments().remove_hint(
            self.item_status_comment.currentText()
        )
        numbers = not_started_numbers
        old_numbers = []
        obj = race()
        for number in numbers:
            if number not in old_numbers:
                person = race().find_person_by_bib(number)
                if person:
                    result = race().new_result(ResultManual)
                    result.person = person
                    result.status = ResultStatus.DID_NOT_START
                    result.status_comment = status_comment
                    live_client.send(result)
                    Teamwork().send(result.to_dict())
                    obj.add_new_result(result)
                else:
                    logging.info("Number %s not found", str(number))
                old_numbers.append(number)
        recalculate_results(recheck_results=False)

    def parse_input_numbers(self):
        text = self.item_numbers.toPlainText()
        numbers = []
        for item in filter(None, text.splitlines()):
            for n_item in item.split():
                if n_item.isdigit():
                    numbers.append(int(n_item))
        return numbers
