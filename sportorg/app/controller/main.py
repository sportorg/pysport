from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QSize
import configparser

import config
from sportorg.language import _, get_languages


class MainWindow(QMainWindow):
    
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.conf = configparser.ConfigParser()

    def show(self):
        self.init_ui()
        super().show()

    def init_ui(self):
        self.setMinimumSize(QSize(480, 320))
        self.setGeometry(480, 320, 480, 320)
        self.setWindowIcon(QIcon(config.ICON))
        self.setWindowTitle("SportOrg")

    def closeEvent(self, *args, **kwargs):
        print(self.geometry())
        super().closeEvent(*args, **kwargs)

