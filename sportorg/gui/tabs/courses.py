import logging

from PySide2 import QtCore, QtWidgets
from PySide2.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.gui.dialogs.course_edit import CourseEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.tabs.memory_model import CourseMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.models.memory import race


class CoursesTableView(TableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = []


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.course_table = CoursesTableView(self)
        self.course_layout = QtWidgets.QGridLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)

        self.course_table.setObjectName('CourseTable')
        self.course_table.setModel(CourseMemoryModel())
        self.course_table.setSortingEnabled(True)
        self.course_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # hor_header = self.course_table.horizontalHeader()
        # assert (isinstance(hor_header, QHeaderView))
        # hor_header.setSectionsMovable(True)
        # hor_header.setDropIndicatorShown(True)
        # hor_header.setSectionResizeMode(QHeaderView.Interactive)
        #
        # ver_header = self.course_table.verticalHeader()
        # ver_header.setSectionResizeMode(QHeaderView.ResizeToContents)

        def course_double_clicked(index):
            try:
                if index.row() < len(race().courses):
                    dialog = CourseEditDialog(race().courses[index.row()])
                    dialog.exec_()
            except Exception as e:
                logging.error(str(e))

        self.course_table.activated.connect(course_double_clicked)
        self.course_layout.addWidget(self.course_table)

    def get_table(self):
        return self.course_table
