import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QDialog, QDialogButtonBox, QTextEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.constant import RentCards


class RentCardsDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Rent cards'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_cards = QLabel('\n\n8654842\n8654844\n8654815\n8654825\n...\n1654815')
        self.item_cards = QTextEdit()
        self.item_cards.setPlainText(RentCards().to_text())

        self.layout.addRow(self.label_cards, self.item_cards)

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
        text = self.item_cards.toPlainText()
        RentCards().set_from_text(text)
        GlobalAccess().get_main_window().refresh()
        with open(config.data_dir('rent_cards.txt'), 'w', encoding='utf-8') as f:
            f.write(RentCards().to_text())
