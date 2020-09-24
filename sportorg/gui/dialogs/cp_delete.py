import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QTextEdit,
)

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.memory import race
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.result_checker import ResultChecker
from sportorg.models.result.score_calculation import ScoreCalculation
from sportorg.models.result.split_calculation import RaceSplits


class CPDeleteDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate('Delete CP'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.item_number = QSpinBox()
        self.item_number.setMaximum(10000)
        self.item_number.valueChanged.connect(self.show_info)
        self.layout.addRow(QLabel(translate('Number CP')), self.item_number)

        self.item_is_course = QCheckBox(translate('Courses'))
        self.item_is_course.setChecked(True)
        self.item_is_course.stateChanged.connect(self.show_info)
        self.layout.addRow(self.item_is_course)

        self.item_is_result = QCheckBox(translate('Race Results'))
        self.item_is_result.setChecked(True)
        self.item_is_result.stateChanged.connect(self.show_info)
        self.layout.addRow(self.item_is_result)

        self.item_info = QTextEdit()
        self.item_info.setReadOnly(True)
        self.layout.addRow(self.item_info)

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
        self.button_ok.setText(translate('Ok'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def show_info(self):
        self.item_info.setText('')
        number = self.item_number.value()
        if not number:
            return
        try:
            text = ''
            is_course = self.item_is_course.isChecked()
            if is_course:
                courses = race().courses
                courses_has_number = []
                for course in courses:
                    for control in course.controls:
                        if str(number) == control.code:
                            courses_has_number.append(course)
                            break
                if len(courses_has_number):
                    text += '{}:\n{}\n'.format(
                        translate('Courses'),
                        '\n'.join([course.name for course in courses_has_number]),
                    )
            is_result = self.item_is_result.isChecked()
            if is_result:
                results = race().results
                results_has_number = []
                for result in results:
                    for split in result.splits:
                        if str(number) == str(split.code):
                            results_has_number.append(result)
                            break
                if len(results_has_number):
                    text += '{}:\n{}'.format(
                        translate('Results'),
                        '\n'.join(
                            [str(result.card_number) for result in results_has_number]
                        ),
                    )
            self.item_info.setText(text)
        except Exception as e:
            logging.error(str(e))
            self.close()

    def apply_changes_impl(self):
        number = self.item_number.value()
        if not number:
            return

        obj = race()

        is_course = self.item_is_course.isChecked()
        if is_course:
            courses = obj.courses
            for course in courses:
                controls = []
                for i, control in enumerate(course.controls):
                    if str(number) == control.code:
                        if i < len(course.controls) - 1:
                            course.controls[i + 1].length += control.length
                        logging.info('Del {} from {}'.format(number, course.name))
                    else:
                        controls.append(control)
                course.controls = controls

        is_result = self.item_is_result.isChecked()
        if is_result:
            results = obj.results
            for result in results:
                splits = []
                for split in result.splits:
                    if str(number) == str(split.code):
                        logging.info(
                            'Del {} from {} {}'.format(
                                number, result.card_number, split.time
                            )
                        )
                    else:
                        splits.append(split)
                result.splits = splits

        obj.clear_results()
        ResultChecker.check_all()
        ResultCalculation(obj).process_results()
        RaceSplits(obj).generate()
        ScoreCalculation(obj).calculate_scores()
