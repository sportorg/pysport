import logging
import traceback

import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.app.controllers.dialogs.course_edit import CourseEditDialog
from sportorg.app.models.memory_model import CourseMemoryModel


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setToolTip("")
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)
        self.course_layout = QtWidgets.QGridLayout(self)
        self.course_layout.setObjectName("course_layout")

        self.CourseTable = QtWidgets.QTableView(self)
        self.CourseTable.setObjectName("CourseTable")
        self.CourseTable.setModel(CourseMemoryModel())
        self.CourseTable.setSortingEnabled(True)
        self.CourseTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        hor_header = self.CourseTable.horizontalHeader()
        assert (isinstance(hor_header, QHeaderView))
        hor_header.setSectionsMovable(True)
        hor_header.setDropIndicatorShown(True)
        hor_header.setSectionResizeMode(QHeaderView.ResizeToContents)

        def course_double_clicked(index):
            print('Courses - clicked on ' + str(index.row()))
            logging.info('Courses - clicked on ' + str(index.row()))
            try:
                dialog = CourseEditDialog(self.CourseTable, index)
                dialog.exec()
            except:
                traceback.print_exc()

        self.CourseTable.doubleClicked.connect(course_double_clicked)
        self.course_layout.addWidget(self.CourseTable)

    def get_table(self):
        return self.CourseTable
