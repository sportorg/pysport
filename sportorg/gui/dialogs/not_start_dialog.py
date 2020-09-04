import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QTextEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import translate
from sportorg.models.constant import StatusComments
from sportorg.models.memory import ResultManual, ResultStatus, find, race


class NotStartDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate('Not started numbers'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.item_status_comment = AdvComboBox()
        self.item_status_comment.addItems(StatusComments().get_all())

        self.layout.addRow(self.item_status_comment)

        self.label_controls = QLabel('\n\n1 4 15 25\n58 32\n33\n34\n...\n150')
        self.item_numbers = QTextEdit()

        self.layout.addRow(self.label_controls, self.item_numbers)

        def cancel_changes():
            self.person = None
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.error(str(e))
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
        status_comment = StatusComments().remove_hint(
            self.item_status_comment.currentText()
        )
        text = self.item_numbers.toPlainText()
        numbers = []
        for item in text.split('\n'):
            if not len(item):
                continue
            for n_item in item.split():
                if n_item.isdigit():
                    numbers.append(int(n_item))
        old_numbers = []
        obj = race()
        for number in numbers:
            if number not in old_numbers:
                person = find(obj.persons, bib=number)
                if person:
                    result = race().new_result(ResultManual)
                    result.person = person
                    result.status = ResultStatus.DID_NOT_START
                    result.status_comment = status_comment
                    obj.add_new_result(result)
                else:
                    logging.info('{} not found'.format(number))
                old_numbers.append(number)
