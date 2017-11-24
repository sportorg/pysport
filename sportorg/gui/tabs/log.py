from PyQt5 import QtCore, QtWidgets, QtGui


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = None
        self.textEdit = None
        self.setup_ui()

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)
        self.layout = QtWidgets.QGridLayout(self)
        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.textEdit.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.layout.addWidget(self.textEdit)

    def write(self, s):
        self.textEdit.setFontWeight(QtGui.QFont.Normal)
        self.textEdit.append(s)
