from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import QPoint
from PySide2.QtWidgets import QAbstractItemView, QHeaderView, QMenu


class TableView(QtWidgets.QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = []
        self.setWordWrap(False)
        self.setAcceptDrops(False)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        hor_header = self.horizontalHeader()
        hor_header.setSectionsMovable(True)
        hor_header.setDropIndicatorShown(True)
        hor_header.setSectionResizeMode(QHeaderView.Interactive)

        ver_header = self.verticalHeader()
        ver_header.setSectionResizeMode(QHeaderView.Fixed)
        ver_header.setDefaultSectionSize(20)

    def mousePressEvent(self, qmouseevent):
        super().mousePressEvent(qmouseevent)
        bt = qmouseevent.button()
        if bt == 2:
            menu = QMenu(self)
            for action in self.popup_items:
                _action = menu.addAction(action[0])
                _action.triggered.connect(action[1])

            point = QPoint(qmouseevent.globalX(), qmouseevent.globalY())
            menu.popup(point)

    def setModel(self, QAbstractItemModel):
        super(TableView, self).setModel(QAbstractItemModel)
        self.resizeColumnsToContents()
