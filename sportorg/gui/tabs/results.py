import logging

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtWidgets import QAbstractItemView, QTextEdit
except ModuleNotFoundError:
    from PySide2 import QtCore, QtGui, QtWidgets
    from PySide2.QtWidgets import QAbstractItemView, QTextEdit

from sportorg.common.otime import OTime
from sportorg.gui.dialogs.result_edit import ResultEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.tabs.memory_model import ResultMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.language import translate
from sportorg.models.memory import Result, race
from sportorg.utils.time import time_to_hhmmss


class ResultsTable(TableView):
    def __init__(self, parent, obj):
        super().__init__(obj)

        self.parent_widget = parent
        self.setObjectName("ResultTable")

        self.setModel(ResultMemoryModel())
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.clicked.connect(self.entry_single_clicked)
        self.activated.connect(self.double_clicked)

        self.popup_items = []

    def update_splits(self):
        if -1 < self.currentIndex().row() < len(race().results):
            self.parent_widget.show_splits(self.currentIndex())

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        try:
            if event.key() == QtCore.Qt.Key_Up or event.key() == QtCore.Qt.Key_Down:
                self.entry_single_clicked(self.currentIndex())
        except Exception as e:
            logging.error(str(e))

    def entry_single_clicked(self, index):
        try:
            #  show splits in the left area
            if -1 < index.row() < len(race().results):
                self.parent_widget.show_splits(index)
        except Exception as e:
            logging.error(str(e))

    def double_clicked(self, index):
        try:
            logging.debug("Clicked on %s", str(index.row()))
            if index.row() < len(race().results):
                dialog = ResultEditDialog(race().results[index.row()])
                dialog.exec_()
                GlobalAccess().get_main_window().refresh()
                # self.selectRow(index.row()+1)
        except Exception as e:
            logging.error(str(e))


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.result_card_form = QtWidgets.QFormLayout()
        self.result_course_form = QtWidgets.QFormLayout()
        self.grid_layout = QtWidgets.QGridLayout(self)
        self.result_splitter = QtWidgets.QSplitter(self)
        self.result_course_group_box = QtWidgets.QGroupBox(self.result_splitter)
        self.result_card_group_box = QtWidgets.QGroupBox(self.result_splitter)
        self.result_table = ResultsTable(self, self.result_splitter)
        self.result_card_details = QtWidgets.QTextBrowser(self.result_card_group_box)
        self.result_card_finish_edit = QtWidgets.QLineEdit(self.result_card_group_box)
        self.result_card_finish_label = QtWidgets.QLabel(self.result_card_group_box)
        self.result_card_start_edit = QtWidgets.QLineEdit(self.result_card_group_box)
        self.result_card_start_label = QtWidgets.QLabel(self.result_card_group_box)
        self.vertical_layout_card = QtWidgets.QVBoxLayout(self.result_card_group_box)
        self.result_course_details = QtWidgets.QTextBrowser(
            self.result_course_group_box
        )
        self.result_course_length_edit = QtWidgets.QLineEdit(
            self.result_course_group_box
        )
        self.result_course_length_label = QtWidgets.QLabel(self.result_course_group_box)
        self.result_course_name_edit = QtWidgets.QLineEdit(self.result_course_group_box)
        self.result_course_name_label = QtWidgets.QLabel(self.result_course_group_box)
        self.vertical_layout_course = QtWidgets.QVBoxLayout(
            self.result_course_group_box
        )
        self.setup_ui()

    def setup_ui(self):
        self.result_splitter.setOrientation(QtCore.Qt.Horizontal)
        self.result_course_name_edit.setAlignment(QtCore.Qt.AlignLeft)
        self.result_course_name_edit.setMinimumWidth(46)
        self.result_course_length_edit.setMinimumWidth(46)
        self.result_splitter.setStretchFactor(2, 100)
        self.result_splitter.setSizes([100, 195, self.result_table.maximumWidth()])

        self.vertical_layout_course.setContentsMargins(0, 0, 0, 0)
        self.vertical_layout_course.setSpacing(0)
        self.result_course_form.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, self.result_course_name_label
        )
        self.result_course_name_edit.setReadOnly(True)
        self.result_course_form.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.result_course_name_edit
        )
        self.result_course_form.setWidget(
            1, QtWidgets.QFormLayout.LabelRole, self.result_course_length_label
        )
        self.result_course_length_edit.setReadOnly(True)
        self.result_course_form.setWidget(
            1, QtWidgets.QFormLayout.FieldRole, self.result_course_length_edit
        )
        self.vertical_layout_course.addLayout(self.result_course_form)

        font = QtGui.QFont()
        font.setFamily("Courier New")
        self.result_course_details.setFont(font)
        self.vertical_layout_course.addWidget(self.result_course_details)
        self.vertical_layout_card.setContentsMargins(0, 0, 0, 0)
        self.vertical_layout_card.setSpacing(0)
        self.result_card_form.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, self.result_card_start_label
        )
        self.result_card_start_edit.setReadOnly(True)
        self.result_card_form.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.result_card_start_edit
        )
        self.result_card_form.setWidget(
            1, QtWidgets.QFormLayout.LabelRole, self.result_card_finish_label
        )
        self.result_card_finish_edit.setReadOnly(True)
        self.result_card_form.setWidget(
            1, QtWidgets.QFormLayout.FieldRole, self.result_card_finish_edit
        )
        self.vertical_layout_card.addLayout(self.result_card_form)
        self.result_card_details.setLineWrapMode(QTextEdit.NoWrap)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        self.result_card_details.setFont(font)
        self.vertical_layout_card.addWidget(self.result_card_details)

        self.grid_layout.addWidget(self.result_splitter)
        self.result_course_group_box.setTitle(translate("Course"))
        self.result_course_name_label.setText(translate("Name"))
        self.result_course_length_label.setText(translate("Length"))
        self.result_card_group_box.setTitle(translate("Chip"))
        self.result_card_start_label.setText(translate("Start"))
        self.result_card_finish_label.setText(translate("Finish"))

        self.result_course_group_box.setMinimumHeight(150)
        self.result_card_group_box.setMinimumHeight(150)

    def show_splits(self, index):
        result: Result = race().results[index.row()]
        self.result_card_details.clear()
        self.result_card_finish_edit.setText("")
        self.result_card_start_edit.setText("")

        self.result_course_details.clear()
        self.result_course_details.setLineWrapMode(QTextEdit.NoWrap)
        self.result_course_name_edit.setText("")
        self.result_course_length_edit.setText("")

        if result.is_manual():
            return

        course = None
        if result.person:
            course = race().find_course(result)

        control_codes = []
        is_highlight = True
        if course:
            is_highlight = not course.is_unknown()
            for control in course.controls:
                control_codes.append(str(control.code))

        time_accuracy = race().get_setting("time_accuracy", 0)
        code = ""
        last_correct_time = OTime()

        start_fmt = "{name:<8} {time}"
        start_time = result.get_start_time()
        start_str = start_fmt.format(
            name=translate("Start"), time=start_time.to_str(time_accuracy)
        )
        self.result_card_details.append(start_str)

        str_fmt_correct = "{index:02d} {code} {time} {diff}"
        str_fmt_incorrect = "-- {code} {time}"
        index = 1
        for split in result.splits:
            str_fmt = str_fmt_correct
            if not split.is_correct:
                str_fmt = str_fmt_incorrect

            s = str_fmt.format(
                index=index,
                code=("(" + str(split.code) + ")   ")[:5],
                time=split.time.to_str(time_accuracy),
                diff=split.leg_time.to_str(time_accuracy),
                leg_place=split.leg_place,
                speed=split.speed,
            )
            if split.is_correct:
                index += 1
                last_correct_time = split.time

            if split.code == code:
                s = '<span style="background: red">{}</span>'.format(s)
            if is_highlight and len(control_codes) and split.code not in control_codes:
                s = '<span style="background: yellow">{}</span>'.format(s)

            self.result_card_details.append(s)
            code = split.code

        finish_time = result.get_finish_time()
        finish_leg = finish_time - last_correct_time
        finish_fmt = "{name:<8} {time} {diff}"
        finish_str = finish_fmt.format(
            name=translate("Finish"),
            time=finish_time.to_str(time_accuracy),
            diff=finish_leg.to_str(time_accuracy),
        )
        self.result_card_details.append(finish_str)

        self.result_card_finish_edit.setText(time_to_hhmmss(result.get_finish_time()))
        self.result_card_start_edit.setText(time_to_hhmmss(result.get_start_time()))

        split_codes = []
        for split in result.splits:
            split_codes.append(split.code)

        start_str = translate("Start")
        self.result_course_details.append(start_str)
        if course:
            index = 1
            for control in course.controls:
                s = "{index:02d} ({code}) {length}".format(
                    index=index,
                    code=control.code,
                    length=control.length if control.length else "",
                )
                if is_highlight and str(control.code) not in split_codes:
                    s = '<span style="background: yellow">{}</span>'.format(s)
                self.result_course_details.append(s)
                index += 1

            self.result_course_name_edit.setText(course.name)
            self.result_course_name_edit.setCursorPosition(0)
            self.result_course_length_edit.setText(str(course.length))
        finish_str = translate("Finish")
        self.result_course_details.append(finish_str)
