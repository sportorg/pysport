import logging
import sys

from PySide2.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
)

from sportorg.libs.winorient.wdb_online_sender import WdbOnlineSender


class WdbOnlineSenderDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Online sender')
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.file_button = QPushButton('Select wdb file')

        def select_file():
            result = QFileDialog.getOpenFileName(
                None, 'select wdb file', '', 'WDB Winorient (*.wdb)'
            )[0]
            self.file_path.setText(result)

        self.file_button.clicked.connect(select_file)
        self.file_path = QLineEdit()
        self.layout.addRow(self.file_button, self.file_path)

        self.url_label = QLabel('URL')
        # self.url_item = QLineEdit('http://orgeo.ru/online/sv?id=20000&sk=20000&sub=1&')
        self.url_item = QLineEdit('http://orgeo.ru/online/sv?id=5651&sk=05c15&sub=1&')
        self.url_item.setMinimumWidth(300)
        self.layout.addRow(self.url_label, self.url_item)

        self.log_area = QTextEdit()
        self.layout.addRow(self.log_area)

        def cancel_changes():
            self.close()

        def start():
            try:
                self.start()
            except Exception as e:
                logging.error(str(e))

        self.button_ok = QPushButton('Start')
        self.button_ok.clicked.connect(start)
        self.button_cancel = QPushButton('Cancel')
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

        self.online_sender = WdbOnlineSender()

        self.show()

    def start(self):
        file_path = self.file_path.text()
        url = self.url_item.text()

        self.online_sender.file_path = file_path
        self.online_sender.url = url
        self.online_sender.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    logging.basicConfig(level=logging.DEBUG)
    WdbOnlineSenderDialog().exec_()
