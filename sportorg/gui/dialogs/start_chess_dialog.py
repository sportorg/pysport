import codecs
import logging
import sys
import time

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QApplication, QDialog, QPushButton, QTextEdit

from sportorg import config
from sportorg.gui.dialogs.file_dialog import get_save_file_name
from sportorg.language import _
from sportorg.models.start.start_calculation import get_chess_list


class StartChessDialog(QDialog):
    def __init__(self):
        super().__init__()

    def exec(self):
        self.init_ui()
        return super().exec()

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
                logging.exception(str(e))
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
        for time_str in sorted(data):
            text += time_str + ' '
            for item in data[time_str]:
                text += str(item['bib']) + ' '
            text += '\n'

        self.text.setText(text)

    def apply_changes_impl(self):
        file_name = get_save_file_name(_('Save As TXT file'), _("Txt file (*.txt)"),
                                       '{}_start_times'.format(time.strftime("%Y%m%d")))
        if file_name:
            with codecs.open(file_name, 'w', 'utf-8') as file:
                file.write(self.text.toPlainText())
                file.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StartChessDialog()
    sys.exit(app.exec_())
