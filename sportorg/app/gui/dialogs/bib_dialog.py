import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QDialog, QPushButton, QSpinBox

from sportorg.app.models import memory
from sportorg.language import _
from sportorg import config


class BibDialog(QDialog):
    def __init__(self, text=''):
        super().__init__()
        self.bib = 0
        self.text = text
        self.person = None
        self.init_ui()

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle(_('Bib'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        if self.text:
            self.label_text = QLabel(self.text)
            self.layout.addRow(self.label_text)

        self.label_bib = QLabel(_('Bib'))
        self.item_bib = QSpinBox()
        self.item_bib.setMaximum(99999)
        self.item_bib.setValue(self.bib)
        self.item_bib.valueChanged.connect(self.show_person_info)
        self.layout.addRow(self.label_bib, self.item_bib)

        self.label_person_info = QLabel('')
        self.layout.addRow(self.label_person_info)

        def cancel_changes():
            self.person = None
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

    def show_person_info(self):
        bib = self.item_bib.value()
        self.label_person_info.setText('')
        if bib:
            person = memory.find(memory.race().persons, bib=bib)
            if person:
                info = person.full_name
                if person.group:
                    info = '{}\n{}: {}'.format(info, _('Group'), person.group.name)
                if person.card_number:
                    info = '{}\n{}: {}'.format(info, _('Card'), person.card_number)
                self.label_person_info.setText(info)
                self.person = person
            else:
                self.label_person_info.setText(_('not found'))

    def get_bib(self):
        return self.bib

    def get_person(self):
        return self.person

    def found_person(self):
        return self.person is not None

    def apply_changes_impl(self):
        pass
