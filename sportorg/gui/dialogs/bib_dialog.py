import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models import memory


class BibDialog(QDialog):
    def __init__(self, text=''):
        super().__init__(GlobalAccess().get_main_window())
        self.text = text
        self.person = None
        self.tmp_person = None

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate('Bib or Name'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        if self.text:
            self.label_text = QLabel(self.text)
            self.layout.addRow(self.label_text)

        self.label_bib_or_name = QLabel(translate('Bib or Name'))
        self.item_bib_or_name = QLineEdit()
        self.item_bib_or_name.selectAll()
        self.item_bib_or_name.textChanged.connect(self.show_person_info)
        self.layout.addRow(self.label_bib_or_name, self.item_bib_or_name)

        self.label_person_info = QLabel('')
        self.layout.addRow(self.label_person_info)

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
        self.button_ok.setText(translate('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def show_person_info(self):
        bib_or_name = self.item_bib_or_name.text()  # type: str
        self.label_person_info.setText('')
        person = None
        if bib_or_name:
            if bib_or_name.isdigit():
                person = memory.find(memory.race().persons, bib=int(bib_or_name))
            else:
                for p in memory.race().persons:
                    if bib_or_name.lower() in p.full_name.lower():
                        person = p
                        break

            if person:
                info = person.full_name
                if person.group:
                    info = '{}\n{}: {}'.format(
                        info, translate('Group'), person.group.name
                    )
                if person.card_number:
                    info = '{}\n{}: {}'.format(
                        info, translate('Card'), person.card_number
                    )
                self.label_person_info.setText(info)
            else:
                self.label_person_info.setText(translate('not found'))
        self.tmp_person = person

    def get_person(self):
        return self.person

    def found_person(self):
        return self.person

    def apply_changes_impl(self):
        self.person = self.tmp_person
