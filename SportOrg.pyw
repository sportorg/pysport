import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from sportorg.app.controller.main import MainWindow


def main(argv):
    app = QApplication(argv)
    main_window = MainWindow(argv)
    main_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main(sys.argv)
