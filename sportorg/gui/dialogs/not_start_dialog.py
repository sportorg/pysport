import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QDialog, QDialogButtonBox, QTextEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.memory import race, ResultStatus, find, ResultSportident
from sportorg.modules.teamwork import Teamwork


class NotStartDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Not started numbers'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

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
        self.button_ok.setText(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def apply_changes_impl(self):
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
                    result = ResultSportident()
                    result.person = person
                    result.status = ResultStatus.DID_NOT_START
                    Teamwork().send(result.to_dict())
                    obj.add_new_result(result)
                else:
                    logging.info('{} not found'.format(number))
                old_numbers.append(number)
        GlobalAccess().get_main_window().refresh()
