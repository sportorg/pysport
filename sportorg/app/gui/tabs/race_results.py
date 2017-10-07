import logging

from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QAbstractItemView, QTableView

from sportorg.app.gui.dialogs.results_edit import ResultEditDialog
from sportorg.app.models.memory import race, Result, Course, CourseControl
from sportorg.app.models.memory_model import ResultMemoryModel
from sportorg.language import _


class ResultTable(QTableView):
    def __init__(self, parent, obj):
        super().__init__(obj)

        self.parent_widget = parent
        self.setObjectName("ResultTable")

        self.setModel(ResultMemoryModel())
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.clicked.connect(self.entry_single_clicked)
        self.activated.connect(self.double_clicked)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        try:
            if event.key() == QtCore.Qt.Key_Up or event.key() == QtCore.Qt.Key_Down:
                self.entry_single_clicked(self.currentIndex())
        except Exception as e:
            logging.exception(str(e))

    def entry_single_clicked(self, index):
        try:
            logging.debug('Single result clicked on ' + str(index.row()))
            #  show punches in the left area
            self.parent_widget.show_punches(index)
        except Exception as e:
            logging.exception(str(e))

        logging.debug('Finish single result clicked on ' + str(index.row()))

    def double_clicked(self, index):
        try:
            logging.debug('Clicked on ' + str(index.row()))
            dialog = ResultEditDialog(self, index)
            dialog.exec()
        except Exception as e:
            logging.exception(str(e))


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.ResultSplitter = QtWidgets.QSplitter(self)
        self.ResultSplitter.setOrientation(QtCore.Qt.Horizontal)
        self.ResultSplitter.setObjectName("ResultSplitter")
        self.ResultLeftPart = QtWidgets.QFrame(self.ResultSplitter)
        self.ResultLeftPart.setMaximumSize(QtCore.QSize(350, 16777215))
        self.ResultLeftPart.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.ResultLeftPart.setFrameShadow(QtWidgets.QFrame.Raised)
        self.ResultLeftPart.setObjectName("ResultLeftPart")
        self.ResultCourseGroupBox = QtWidgets.QGroupBox(self.ResultLeftPart)
        self.ResultCourseGroupBox.setGeometry(QtCore.QRect(1, 1, 120, 399))
        self.ResultCourseGroupBox.setObjectName("ResultCourseGroupBox")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.ResultCourseGroupBox)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.ResultCourseForm = QtWidgets.QFormLayout()
        self.ResultCourseForm.setObjectName("ResultCourseForm")
        self.ResultCourseNameLabel = QtWidgets.QLabel(self.ResultCourseGroupBox)
        self.ResultCourseNameLabel.setObjectName("ResultCourseNameLabel")
        self.ResultCourseForm.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.ResultCourseNameLabel)
        self.ResultCourseNameEdit = QtWidgets.QLineEdit(self.ResultCourseGroupBox)
        self.ResultCourseNameEdit.setObjectName("ResultCourseNameEdit")
        self.ResultCourseForm.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.ResultCourseNameEdit)
        self.ResultCourseLengthLabel = QtWidgets.QLabel(self.ResultCourseGroupBox)
        self.ResultCourseLengthLabel.setObjectName("ResultCourseLengthLabel")
        self.ResultCourseForm.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.ResultCourseLengthLabel)
        self.ResultCourseLengthEdit = QtWidgets.QLineEdit(self.ResultCourseGroupBox)
        self.ResultCourseLengthEdit.setObjectName("ResultCourseLengthEdit")
        self.ResultCourseForm.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.ResultCourseLengthEdit)
        self.verticalLayout_2.addLayout(self.ResultCourseForm)
        self.ResultCourseDetails = QtWidgets.QTextBrowser(self.ResultCourseGroupBox)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        self.ResultCourseDetails.setFont(font)
        self.ResultCourseDetails.setObjectName("ResultCourseDetails")
        self.verticalLayout_2.addWidget(self.ResultCourseDetails)
        self.ResultChipGroupBox = QtWidgets.QGroupBox(self.ResultLeftPart)
        self.ResultChipGroupBox.setGeometry(QtCore.QRect(120, 1, 300, 399))
        self.ResultChipGroupBox.setObjectName("ResultChipGroupBox")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.ResultChipGroupBox)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.ResultChipForm = QtWidgets.QFormLayout()
        self.ResultChipForm.setObjectName("ResultChipForm")
        self.ResultChipStartLabel = QtWidgets.QLabel(self.ResultChipGroupBox)
        self.ResultChipStartLabel.setObjectName("ResultChipStartLabel")
        self.ResultChipForm.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.ResultChipStartLabel)
        self.ResultChipStartEdit = QtWidgets.QLineEdit(self.ResultChipGroupBox)
        self.ResultChipStartEdit.setObjectName("ResultChipStartEdit")
        self.ResultChipForm.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.ResultChipStartEdit)
        self.ResultChipFinishLabel = QtWidgets.QLabel(self.ResultChipGroupBox)
        self.ResultChipFinishLabel.setObjectName("ResultChipFinishLabel")
        self.ResultChipForm.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.ResultChipFinishLabel)
        self.ResultChipFinishEdit = QtWidgets.QLineEdit(self.ResultChipGroupBox)
        self.ResultChipFinishEdit.setObjectName("ResultChipFinishEdit")
        self.ResultChipForm.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.ResultChipFinishEdit)
        self.verticalLayout_3.addLayout(self.ResultChipForm)
        self.ResultChipDetails = QtWidgets.QTextBrowser(self.ResultChipGroupBox)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        self.ResultChipDetails.setFont(font)
        self.ResultChipDetails.setObjectName("ResultChipDetails")
        self.verticalLayout_3.addWidget(self.ResultChipDetails)
        self.ResultTable = ResultTable(self, self.ResultSplitter)

        self.gridLayout.addWidget(self.ResultSplitter)
        self.ResultCourseGroupBox.setTitle(_("Course"))
        self.ResultCourseNameLabel.setText(_("Name"))
        self.ResultCourseLengthLabel.setText(_("Length"))
        # self.ResultCourseDetails.setHtml()
        self.ResultChipGroupBox.setTitle(_("Chip"))
        self.ResultChipStartLabel.setText(_("Start"))
        self.ResultChipFinishLabel.setText(_("Finish"))
        # self.ResultChipDetails.setHtml()

    def show_punches(self, index):

        assert (isinstance(index, QModelIndex))
        orig_index_int = index.row()

        result = race().results[orig_index_int]
        assert isinstance(result, Result)
        self.ResultChipDetails.clear()
        index = 1
        for i in result.punches:
            time = i[1]
            assert isinstance(time, datetime)
            s = str(index) + " " + str(i[0]) + " " + time.strftime("%H:%M:%S")
            self.ResultChipDetails.append(s)
            index += 1
        if result.finish_time:
            self.ResultChipFinishEdit.setText(result.finish_time.strftime("%H:%M:%S"))
        if result.start_time:
            self.ResultChipStartEdit.setText(result.start_time.strftime("%H:%M:%S"))

        self.ResultCourseDetails.clear()
        index = 1
        if result.person and result.person.group and result.person.group.course:
            course = result.person.group.course
            assert isinstance(course, Course)
            if course.controls is not None:
                for i in course.controls:
                    assert isinstance(i, CourseControl)
                    s = str(index) + " " + str(i.code) + " " + str(i.length)
                    self.ResultCourseDetails.append(s)
                    index += 1
            self.ResultCourseNameEdit.setText(course.name)
            self.ResultCourseLengthEdit.setText(str(course.length))
