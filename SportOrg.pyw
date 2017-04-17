import sys

from PyQt5.QtWidgets import QApplication

from sportorg.app.contoller.main import MainWindow


def main(argv):
    app = QApplication(argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main(sys.argv)
