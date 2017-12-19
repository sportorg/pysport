import logging

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QTableView, QDialogButtonBox, QVBoxLayout, QLineEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _


class SearchDialog(QDialog):

    def __init__(self, table=None):
        super().__init__(GlobalAccess().get_main_window())
        if table is not None:
            self.table = table

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QVBoxLayout(self)

        self.item_serach = QLineEdit()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.clicked.connect(self.accept)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.clicked.connect(self.reject)

        self.layout.addWidget(self.item_serach)
        self.layout.addWidget(button_box)

        self.retranslate_ui()

        self.show()

    def accept(self):
        try:
            if self.table is not None:
                assert (isinstance(self.table, QTableView))
                proxy_model = self.table.model()
                proxy_model.clear_search()

                proxy_model.search = self.item_serach.text()

                proxy_model.apply_search()

                GlobalAccess().get_main_window().refresh()
                logging.info('Search: {}'.format(proxy_model.search))
        except Exception as e:
            logging.exception(str(e))

        self.destroy()

    def reject(self):
        self.destroy()

    def retranslate_ui(self):
        self.setWindowTitle(_("Search"))
        self.button_ok.setText(_('OK'))
        self.button_cancel.setText(_('Cancel'))
