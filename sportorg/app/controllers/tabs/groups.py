import logging
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.app.models.memory_model import PersonProxyModel, GroupMemoryModel


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setToolTip("")
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)
        self.group_layout = QtWidgets.QGridLayout(self)
        self.group_layout.setObjectName("group_layout")


        self.GroupTable = QtWidgets.QTableView(self)
        self.GroupTable.setObjectName("GroupTable")
        proxy_model = PersonProxyModel(self)
        proxy_model.setSourceModel(GroupMemoryModel())
        self.GroupTable.setModel(proxy_model)
        self.GroupTable.setSortingEnabled(True)
        self.GroupTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        hor_header = self.GroupTable.horizontalHeader()
        assert (isinstance(hor_header, QHeaderView))
        hor_header.setSectionsMovable(True)
        hor_header.setDropIndicatorShown(True)
        hor_header.setSectionResizeMode(QHeaderView.ResizeToContents)

        def group_double_clicked(index):
            print('clicked on ' + str(index.row()))
            logging.info('clicked on ' + str(index.row()))
            # show_edit_dialog(index)
            # try:
            #      dialog = GroupEditDialog(self.GroupTable, index)
            # except:
            #     print(sys.exc_info())
            #     traceback.print_stack()

            #dialog.exec()

        self.GroupTable.doubleClicked.connect(group_double_clicked)
        self.group_layout.addWidget(self.GroupTable)

    def get_table(self):
        return self.GroupTable
