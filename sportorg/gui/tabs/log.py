try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    from PySide2 import QtCore, QtGui, QtWidgets

from sportorg.modules.configs.configs import Config as Configuration


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = None
        self.textEdit = None
        self.setup_ui()
        self.common_color = QtGui.QColor(0, 0, 0, 255)
        self.error_color = QtGui.QColor(255, 0, 0, 240)

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)
        self.layout = QtWidgets.QGridLayout(self)
        self.textEdit = QtWidgets.QPlainTextEdit(self)
        self.textEdit.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.textEdit.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.textEdit.setMaximumBlockCount(
            Configuration().configuration.get("log_window_row_count")
        )
        self.layout.addWidget(self.textEdit)

    def write(self, s):
        self.textEdit.appendPlainText(s)
