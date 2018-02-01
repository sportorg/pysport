import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QDialog, QDialogButtonBox, QCheckBox, QSpinBox, QLabel

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.memory import race
from sportorg.models.result.result_calculation import ResultCalculation


class CPDeleteDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Delete CP'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.item_number = QSpinBox()
        self.item_number.setMaximum(10000)
        self.item_number.valueChanged.connect(self.show_info)
        self.layout.addRow(QLabel(_('Number CP')), self.item_number)

        self.item_is_course = QCheckBox(_('Courses'))
        self.item_is_course.setChecked(True)
        self.layout.addRow(self.item_is_course)

        self.item_is_result = QCheckBox(_('Race Results'))
        self.item_is_result.setChecked(True)
        self.layout.addRow(self.item_is_result)

        self.label_info = QLabel('')
        self.layout.addRow(self.label_info)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(str(e))
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(_('Ok'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def show_info(self):
        self.label_info.setText('')
        number = self.item_number.value()
        if not number:
            return
        courses = race().courses
        courses_has_number = []
        try:
            for course in courses:
                for control in course.controls:
                    if str(number) == control.code:
                        courses_has_number.append(course)
                        break
            if len(courses_has_number):
                self.label_info.setText('{}:\n{}'.format(
                    _('Groups'),
                    '\n'.join([course.name for course in courses_has_number])
                ))
        except Exception as e:
            logging.error(str(e))
            self.close()

    def apply_changes_impl(self):
        number = self.item_number.value()
        if not number:
            return

        is_course = self.item_is_course.isChecked()
        if is_course:
            courses = race().courses
            for course in courses:
                controls = []
                for i, control in enumerate(course.controls):
                    if str(number) == control.code:
                        if i < len(course.controls)-1:
                            course.controls[i+1].length += control.length
                        logging.info('Del {} from {}'.format(number, course.name))
                    else:
                        controls.append(control)
                course.controls = controls

        is_result = self.item_is_result.isChecked()
        if is_result:
            results = race().results
            for result in results:
                if not result.is_sportident():
                    continue
                splits = []
                for split in result.splits:
                    if str(number) == str(split.code):
                        logging.info('Del {} from {} {}'.format(number, result.sportident_card, split.time))
                    else:
                        splits.append(split)
                result.splits = splits

        race().clear_sportident_results()
        ResultCalculation(race()).process_results()
        GlobalAccess().get_main_window().refresh()
