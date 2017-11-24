import logging

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.gui.dialogs.course_edit import CourseEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.tabs.memory_model import CourseMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.language import _
from sportorg.models.memory import race


class CoursesTableView(TableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = [
            (_("Add object"), GlobalAccess().add_object),
            (_('Delete'), GlobalAccess().get_main_window().delete_object)
        ]


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.course_layout = None
        self.CourseTable = None
        self.setup_ui()

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)
        self.course_layout = QtWidgets.QGridLayout(self)
        self.course_layout.setObjectName("course_layout")

        self.CourseTable = CoursesTableView(self)
        self.CourseTable.setObjectName("CourseTable")
        self.CourseTable.setModel(CourseMemoryModel())
        self.CourseTable.setSortingEnabled(True)
        self.CourseTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        hor_header = self.CourseTable.horizontalHeader()
        assert (isinstance(hor_header, QHeaderView))
        hor_header.setSectionsMovable(True)
        hor_header.setDropIndicatorShown(True)
        hor_header.setSectionResizeMode(QHeaderView.Interactive)

        def course_double_clicked(index):
            logging.debug('Courses - clicked on ' + str(index.row()))
            try:
                if index.row() < len(race().courses):
                    dialog = CourseEditDialog(self.CourseTable, index)
                    dialog.exec()
            except Exception as e:
                logging.exception(str(e))

        self.CourseTable.activated.connect(course_double_clicked)
        self.course_layout.addWidget(self.CourseTable)

    def get_table(self):
        return self.CourseTable
