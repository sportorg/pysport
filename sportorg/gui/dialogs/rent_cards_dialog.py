import logging

try:
    from PySide6 import QtCore
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QTextEdit,
    )
except ModuleNotFoundError:
    from PySide2 import QtCore
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QTextEdit,
    )

from sportorg import config, settings
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.constant import RentCards


class RentCardsDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate("Rent cards"))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_cards = QLabel(
            "\n\n8654842\n8654844\n8654815\n8654825\n...\n1654815"
        )
        self.item_cards = QTextEdit()
        self.item_cards.setPlainText(RentCards().to_text())
        self.item_cards.setTabChangesFocus(True)

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
        self.button_ok.setText(translate("OK"))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate("Cancel"))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        QtCore.QTimer.singleShot(0, self.item_cards.setFocus)

        self.show()

    def apply_changes_impl(self):
        text = self.item_cards.toPlainText()
        RentCards().set_from_text(text)
        with open(settings.SETTINGS.source_rent_cards_path, "w", encoding="utf-8") as f:
            f.write(RentCards().to_text())
