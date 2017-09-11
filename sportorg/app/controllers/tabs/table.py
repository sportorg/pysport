from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import QPoint


class TableView(QtWidgets.QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = []

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
