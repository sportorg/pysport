import sys


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from sportorg.gui.main import MainWindow

    app = QApplication(sys.argv)
    main_window = MainWindow(sys.argv)
    main_window.show_window()
    sys.exit(app.exec())
