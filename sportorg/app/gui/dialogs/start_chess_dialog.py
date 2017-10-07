import codecs
import sys
import logging

import time
from PyQt5 import QtWidgets

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QApplication, QDialog, QPushButton, QTextEdit

from sportorg.app.models.start_calculation import get_chess_list

from sportorg.language import _
from sportorg import config


class StartChessDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle(_('Start times'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.text = QTextEdit()
        self.text.setMinimumHeight(450)
        self.text.setMinimumWidth(450)
        self.text.setMaximumHeight(450)
        self.layout.addRow(self.text)

        self.set_text()

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(e)
            self.close()

        self.button_ok = QPushButton(_('Save to file'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

        self.show()

    def set_text(self):
        text = ''
        data = get_chess_list()
        for time in data:
            text += time + ' '
            for item in data[time]:
                text += str(item[0]) + ' '
            text += '\n'

        self.text.setText(text)

    def apply_changes_impl(self):
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, _('Save As TXT file'),
                                                          '/start_times_' + str(time.strftime("%Y%m%d")),
                                                          _("Txt file (*.txt)"))[0]
        with codecs.open(file_name, 'w', 'utf-8') as file:
            file.write(self.text.toPlainText())
            file.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StartChessDialog()
    sys.exit(app.exec_())
