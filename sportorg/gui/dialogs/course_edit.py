import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QFormLayout, QLabel, QLineEdit, QDialog, QSpinBox, QTextEdit, QDialogButtonBox

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.memory import race, Course, CourseControl, find
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.result_checker import ResultChecker
from sportorg.models.result.score_calculation import ScoreCalculation
from sportorg.models.result.split_calculation import RaceSplits
from sportorg.modules.teamwork import Teamwork


class CourseEditDialog(QDialog):
    def __init__(self, course, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        assert (isinstance(course, Course))
        self.current_object = course
        self.is_new = is_new

    def exec_(self):
        self.init_ui()
        self.set_values_from_model()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_('Course properties'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_name = QLabel(_('Name'))
        self.item_name = QLineEdit()
        self.item_name.textChanged.connect(self.check_name)
        self.layout.addRow(self.label_name, self.item_name)

        self.label_length = QLabel(_('Length(m)'))
        self.item_length = QSpinBox()
        self.item_length.setMaximum(100000)
        self.item_length.setSingleStep(100)
        self.item_length.setValue(0)
        self.layout.addRow(self.label_length, self.item_length)

        self.label_climb = QLabel(_('Climb'))
        self.item_climb = QSpinBox()
        self.item_climb.setValue(0)
        self.item_climb.setMaximum(10000)
        self.item_climb.setSingleStep(10)
        self.layout.addRow(self.label_climb, self.item_climb)

        self.label_control_qty = QLabel(_('Point count'))
        self.item_control_qty = QSpinBox()
        self.item_control_qty.setDisabled(True)
        self.layout.addRow(self.label_control_qty, self.item_control_qty)

        self.label_controls = QLabel('{}\n\n31 150\n32 200\n33\n34 500\n...\n90 150'.format(_('Controls')))
        self.item_controls = QTextEdit()
        self.item_controls.setTabChangesFocus(True)
        self.layout.addRow(self.label_controls, self.item_controls)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.error(str(e))
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def check_name(self):
        name = self.item_name.text()
        self.button_ok.setDisabled(False)
        if name and name != self.current_object.name:
            org = find(race().courses, name=name)
            if org:
                self.button_ok.setDisabled(True)

    def set_values_from_model(self):

        self.item_name.setText(self.current_object.name)

        if self.current_object.length:
            self.item_length.setValue(self.current_object.length)
        if self.current_object.climb:
            self.item_climb.setValue(self.current_object.climb)
        if self.current_object.controls:
            self.item_control_qty.setValue(len(self.current_object.controls))
        for i in self.current_object.controls:
            assert isinstance(i, CourseControl)
            self.item_controls.append('{} {}'.format(i.code, i.length if i.length else ''))

    def apply_changes_impl(self):
        course = self.current_object
        if self.is_new:
            race().courses.insert(0, course)

        if course.name != self.item_name.text():
            course.name = self.item_name.text()

        if course.length != self.item_length.value():
            course.length = self.item_length.value()

        if course.climb != self.item_climb.value():
            course.climb = self.item_climb.value()

        text = self.item_controls.toPlainText()

        course.controls.clear()
        for i in text.split('\n'):
            control = CourseControl()
            if i is None or len(i) == 0:
                continue
            control.code = i.split()[0]
            if len(i.split()) > 1:
                try:
                    control.length = int(i.split()[1])
                except Exception as e:
                    logging.error(str(e))
                    control.length = 0
            course.controls.append(control)

        obj = race()
        ResultChecker.check_all()
        ResultCalculation(obj).process_results()
        RaceSplits(obj).generate()
        ScoreCalculation(obj).calculate_scores()
        Teamwork().send(course.to_dict())
