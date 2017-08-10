import sys

from PyQt5.QtWidgets import QApplication

from sportorg import config

from sportorg.app.controllers.main import MainWindow


def main(argv):
    app = QApplication(argv)
    main_window = MainWindow(argv)
    main_window.show_window()
    sys.exit(app.exec())


if __name__ == '__main__':
    main(sys.argv)
