import logging

from PySide2 import QtCore
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate


class SearchDialog(QDialog):
    def __init__(self, table=None):
        super().__init__(GlobalAccess().get_main_window())
        if table:
            self.table = table

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QVBoxLayout(self)

        self.item_serach = QLineEdit()
        if self.table:
            self.item_serach.setText(self.table.model().search)
            self.item_serach.selectAll()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.clicked.connect(self.ok)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.clicked.connect(self.cancel)

        self.layout.addWidget(self.item_serach)
        self.layout.addWidget(button_box)

        self.retranslate_ui()

        self.show()

    def ok(self):
        try:
            if self.table:
                proxy_model = self.table.model()

                proxy_model.search = self.item_serach.text()

                proxy_model.apply_search()
                offset = proxy_model.search_offset
                if offset == -1 and proxy_model.search:
                    QMessageBox.warning(
                        self,
                        translate('Search'),
                        translate('The search has not given any results'),
                    )
                self.table.selectRow(offset)
        except Exception as e:
            logging.error(str(e))

    def cancel(self):
        self.close()

    def retranslate_ui(self):
        self.setWindowTitle(translate('Search'))
        self.button_ok.setText(translate('OK'))
        self.button_cancel.setText(translate('Cancel'))
