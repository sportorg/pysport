from PySide2 import QtWidgets
from PySide2.QtWidgets import QMenu, QAbstractItemView
from PySide2.QtCore import QPoint


class TableView(QtWidgets.QTreeView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = []
        self.setWordWrap(False)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setStyleSheet("*::item{"
                           "    border-top-width: 0px;"
                           "    border-right-width: 1px;"
                           "    border-bottom-width: 1px;"
                           "    border-left-width: 0px;"
                           "    border-style: solid;"
                           "    border-color: silver;"
                           "}"
                           "*::item:selected{"
                           "    background: palette(Highlight);"
                           "}")
        self.setRootIsDecorated(False)

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
        for i in range(self.model().columnCount()):
            self.resizeColumnToContents(i)

    def update_row(self, index):
        #  Refresh QTreeView row
        model = self.model()
        model.beginInsertRows(index.parent(), 0, 0)
        model.endInsertRows()
        self.setCurrentIndex(index)