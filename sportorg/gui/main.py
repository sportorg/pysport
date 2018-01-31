from multiprocessing import freeze_support

import sys
from PyQt5.QtWidgets import QApplication

from sportorg.core.singleton import Singleton
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.main_window import MainWindow


class Application(metaclass=Singleton):
    def __init__(self):
        self.argv = sys.argv
        self.app = QApplication(self.argv)
        self.main_window = MainWindow(self.argv)
        GlobalAccess().set_app(self)

    def get_main_window(self):
        return self.main_window

    def run(self):
        freeze_support()
        self.main_window.show_window()
        sys.exit(self.app.exec())
