import logging

from sportorg.gui.dialogs.dialog import BaseDialog, LineField, NumberField, TextField
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.memory import CourseControl, find, race
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.result_checker import ResultChecker
from sportorg.models.result.score_calculation import ScoreCalculation
from sportorg.models.result.split_calculation import RaceSplits


class CourseEditDialog(BaseDialog):
    def __init__(self, course, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        self.current_object = course
        self.is_new = is_new
        self.title = translate('Course properties')
        self.size = (400, 360)
        self.form = [
            LineField(
                title=translate('Name'),
                object=course,
                key='name',
                id='name',
                select_all=True,
            ),
            NumberField(
                title=translate('Length(m)'),
                object=course,
                key='length',
                maximum=100000,
                single_step=100,
            ),
            NumberField(
                id='climb',
                title=translate('Climb'),
                object=course,
                key='climb',
                maximum=10000,
                single_step=10,
            ),
            NumberField(
                title=translate('Point count'),
                maximum=1000,
                is_disabled=True,
                id='point_count',
            ),
            TextField(
                title='{}\n\n31 150\n32 200\n33\n34 500\n...\n90 150'.format(
                    translate('Controls')
                ),
                object=course,
                key='controls',
                id='controls',
            ),
        ]

    def before_showing(self) -> None:
        self.on_controls_changed()

    def convert_controls(self, controls) -> str:
        result = []
        for i in controls:
            result.append('{} {}'.format(i.code, i.length if i.length else ''))
        return result

    def parse_controls(self, text: str):
        controls = []
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
            controls.append(control)
        return controls

    def on_controls_changed(self):
        text = self.fields['controls'].q_item.toPlainText()
        self.fields['point_count'].q_item.setValue(len(self.parse_controls(text)))

    def on_name_changed(self):
        name = self.fields['name'].q_item.text()
        self.button_ok.setDisabled(False)
        if name and name != self.current_object.name:
            course = find(race().courses, name=name)
            if course:
                self.button_ok.setDisabled(True)

    def apply(self):
        obj = race()
        if self.is_new:
            obj.courses.insert(0, self.current_object)
        ResultChecker.check_all()
        ResultCalculation(obj).process_results()
        RaceSplits(obj).generate()
        ScoreCalculation(obj).calculate_scores()
