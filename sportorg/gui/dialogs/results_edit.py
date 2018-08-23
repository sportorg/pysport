import logging

from abc import abstractmethod

from datetime import datetime

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QLineEdit, QDialog, \
    QTimeEdit, QRadioButton, QSpinBox, QGroupBox, QTextEdit, QDialogButtonBox, QDateTimeEdit

from sportorg import config
from sportorg.gui.dialogs.entry_edit import EntryEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.constant import StatusComments
from sportorg.models.memory import race, Result, find, ResultStatus, Person, Limit, Split
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.result_checker import ResultChecker, ResultCheckerException
from sportorg.models.result.split_calculation import GroupSplits
from sportorg.modules.teamwork import Teamwork
from sportorg.utils.time import time_to_qtime, time_to_otime, hhmmss_to_time


class ResultEditDialog(QDialog):
    def __init__(self, result, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        assert (isinstance(result, Result))
        self.current_object = result
        self.is_new = is_new

        self.time_format = 'hh:mm:ss'
        time_accuracy = race().get_setting('time_accuracy', 0)
        if time_accuracy:
            self.time_format = 'hh:mm:ss.zzz'

    def exec(self):
        self.init_ui()
        self.set_values_from_model()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Result'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.item_created_at = QTimeEdit()
        self.item_created_at.setDisplayFormat(self.time_format)
        self.item_created_at.setReadOnly(True)

        self.item_card_number = QSpinBox()
        self.item_card_number.setMaximum(9999999)

        self.item_bib = QSpinBox()
        self.item_bib.setMaximum(Limit.BIB)
        self.item_bib.valueChanged.connect(self.show_person_info)

        self.label_person_info = QLabel('')

        self.item_days = QSpinBox()
        self.item_days.setMaximum(365)

        self.item_finish = QTimeEdit()
        self.item_finish.setDisplayFormat(self.time_format)

        self.item_start = QTimeEdit()
        self.item_start.setDisplayFormat(self.time_format)

        self.item_result = QLineEdit()
        self.item_result.setEnabled(False)

        self.item_credit = QTimeEdit()
        self.item_credit.setDisplayFormat(self.time_format)

        self.item_penalty = QTimeEdit()
        self.item_penalty.setDisplayFormat(self.time_format)

        self.item_penalty_laps = QSpinBox()
        self.item_penalty_laps.setMaximum(1000000)

        self.radio_ok = QRadioButton(_('OK'))
        self.radio_ok.setChecked(True)
        self.radio_dns = QRadioButton(_('DNS'))
        self.radio_dnf = QRadioButton(_('DNF'))
        self.radio_overtime = QRadioButton(_('Overtime'))
        self.radio_dsq = QRadioButton(_('DSQ'))
        self.item_status_comment = AdvComboBox()
        self.item_status_comment.setMaximumWidth(250)
        self.item_status_comment.view().setMinimumWidth(650)
        self.item_status_comment.addItems(StatusComments().get_all())

        more24 = race().get_setting('time_format_24', 'less24') == 'more24'
        self.splits = SplitsText(more24=more24)

        self.layout.addRow(QLabel(_('Created at')), self.item_created_at)
        if self.current_object.is_punch():
            self.layout.addRow(QLabel(_('Card')), self.item_card_number)
        self.layout.addRow(QLabel(_('Bib')), self.item_bib)
        self.layout.addRow(QLabel(''), self.label_person_info)
        if more24:
            self.layout.addRow(QLabel(_('Days')), self.item_days)
        self.layout.addRow(QLabel(_('Start')), self.item_start)
        self.layout.addRow(QLabel(_('Finish')), self.item_finish)
        self.layout.addRow(QLabel(_('Credit')), self.item_credit)
        self.layout.addRow(QLabel(_('Penalty')), self.item_penalty)
        self.layout.addRow(QLabel(_('Penalty legs')), self.item_penalty_laps)
        self.layout.addRow(QLabel(_('Result')), self.item_result)

        self.layout.addRow(self.radio_ok)
        self.layout.addRow(self.radio_dns)
        self.layout.addRow(self.radio_dnf)
        self.layout.addRow(self.radio_overtime)
        self.layout.addRow(self.radio_dsq, self.item_status_comment)

        if self.current_object.is_punch():
            start_source = race().get_setting('system_start_source', 'protocol')
            finish_source = race().get_setting('system_finish_source', 'station')
            if start_source == 'protocol' or start_source == 'cp':
                self.item_start.setDisabled(True)
            if finish_source == 'cp':
                self.item_finish.setDisabled(True)
            self.layout.addRow(self.splits.widget)

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

        if self.current_object.person:
            button_person = button_box.addButton(_('Entry properties'), QDialogButtonBox.ActionRole)
            button_person.clicked.connect(self.open_person)

        self.layout.addRow(button_box)

        self.show()
        self.item_bib.setFocus()

    def show_person_info(self):
        bib = self.item_bib.value()
        self.label_person_info.setText('')
        if bib:
            person = find(race().persons, bib=bib)
            if person:
                info = person.full_name
                if person.group:
                    info = '{}\n{}: {}'.format(info, _('Group'), person.group.name)
                if person.card_number:
                    info = '{}\n{}: {}'.format(info, _('Card'), person.card_number)
                self.label_person_info.setText(info)
            else:
                self.label_person_info.setText(_('not found'))

    def set_values_from_model(self):
        if self.current_object.is_punch():
            if self.current_object.card_number:
                self.item_card_number.setValue(int(self.current_object.card_number))
            self.splits.splits(self.current_object.splits)
            self.splits.show()
        if self.current_object.created_at:
            self.item_created_at.setTime(time_to_qtime(datetime.fromtimestamp(self.current_object.created_at)))
        if self.current_object.finish_time:
            self.item_finish.setTime(time_to_qtime(self.current_object.finish_time))
        if self.current_object.start_time is not None:
            self.item_start.setTime(time_to_qtime(self.current_object.start_time))
        if self.current_object.finish_time:
            self.item_result.setText(str(self.current_object.get_result()))
        if self.current_object.credit_time is not None:
            self.item_credit.setTime(time_to_qtime(self.current_object.credit_time))
        if self.current_object.penalty_time is not None:
            self.item_penalty.setTime(time_to_qtime(self.current_object.penalty_time))
        if self.current_object.penalty_laps:
            self.item_penalty_laps.setValue(self.current_object.penalty_laps)
        self.item_bib.setValue(self.current_object.get_bib())

        self.item_days.setValue(self.current_object.days)

        if self.current_object.is_status_ok():
            self.radio_ok.setChecked(True)
        elif self.current_object.status == ResultStatus.DISQUALIFIED:
            self.radio_dsq.setChecked(True)
        elif self.current_object.status == ResultStatus.OVERTIME:
            self.radio_overtime.setChecked(True)
        elif self.current_object.status == ResultStatus.DID_NOT_FINISH:
            self.radio_dnf.setChecked(True)
        elif self.current_object.status == ResultStatus.DID_NOT_START:
            self.radio_dns.setChecked(True)

        self.item_status_comment.setCurrentText(self.current_object.status_comment)

        self.item_bib.selectAll()

    def open_person(self):
        try:
            EntryEditDialog(self.current_object.person).exec()
        except Exception as e:
            logging.error(str(e))

    def apply_changes_impl(self):
        result = self.current_object
        if self.is_new:
            race().results.insert(0, result)

        if result.is_punch():
            if result.card_number != self.item_card_number.value():
                result.card_number = self.item_card_number.value()

            new_splits = self.splits.splits()
            if len(result.splits) == len(new_splits):
                for i, split in enumerate(result.splits):
                    if split != new_splits[i]:
                        break
            result.splits = new_splits

        time_ = time_to_otime(self.item_finish.time())
        if result.finish_time != time_:
            result.finish_time = time_

        time_ = time_to_otime(self.item_start.time())
        if result.start_time != time_:
            result.start_time = time_

        time_ = time_to_otime(self.item_credit.time())
        if result.credit_time != time_:
            result.credit_time = time_

        time_ = time_to_otime(self.item_penalty.time())
        if result.penalty_time != time_:
            result.penalty_time = time_

        if result.penalty_laps != self.item_penalty_laps.value():
            result.penalty_laps = self.item_penalty_laps.value()

        cur_bib = -1
        new_bib = self.item_bib.value()
        if result.person:
            cur_bib = result.person.bib

        if new_bib == 0:
            if result.person and result.is_punch():
                if result.person.card_number == result.card_number:
                    result.person.card_number = 0
            result.person = None
        elif cur_bib != new_bib:
            new_person = find(race().persons, bib=new_bib)
            if new_person is not None:
                assert isinstance(new_person, Person)
                if result.person:
                    if result.is_punch():
                        result.person.card_number = 0
                result.person = new_person
                if result.is_punch():
                    race().person_card_number(result.person, result.card_number)
            result.bib = new_bib

            GlobalAccess().get_main_window().get_result_table().model().init_cache()

        if self.item_days.value() != result.days:
            result.days = self.item_days.value()

        status = ResultStatus.NONE
        if self.radio_ok.isChecked():
            status = ResultStatus.OK
        elif self.radio_dsq.isChecked():
            status = ResultStatus.DISQUALIFIED
        elif self.radio_overtime.isChecked():
            status = ResultStatus.OVERTIME
        elif self.radio_dnf.isChecked():
            status = ResultStatus.DID_NOT_FINISH
        elif self.radio_dns.isChecked():
            status = ResultStatus.DID_NOT_START
        if result.status != status:
            result.status = status

        status = StatusComments().remove_hint(self.item_status_comment.currentText())
        if result.status_comment != status:
            result.status_comment = status

        if result.is_punch():
            result.clear()
            try:
                ResultChecker.checking(result)
                ResultChecker.calculate_penalty(result)
                if result.person and result.person.group:
                    GroupSplits(race(), result.person.group).generate(True)
            except ResultCheckerException as e:
                logging.error(str(e))
        ResultCalculation(race()).process_results()
        GlobalAccess().get_main_window().refresh()
        Teamwork().send(result.to_dict())


class SplitsObject:
    @property
    @abstractmethod
    def widget(self):
        pass

    @abstractmethod
    def splits(self, splits=None):
        pass

    @abstractmethod
    def show(self):
        pass


class SplitsText(SplitsObject):
    def __init__(self, splits=None, more24=False):
        self._splits = splits
        self._more24 = more24
        self._box = QGroupBox(_('Splits'))
        self._layout = QFormLayout()
        self._text = QTextEdit()
        self._text.setTabChangesFocus(True)
        self._text.setMinimumHeight(200)
        self._layout.addRow(QLabel(self._get_example_text()), self._text)
        self._box.setLayout(self._layout)

    @property
    def widget(self):
        return self._box

    def splits(self, splits=None):
        if splits is None:
            text_row = self._text.toPlainText().split('\n')
            splits = []
            for row in text_row:
                if not row.strip():
                    continue
                item = row.split()
                if len(item) >= 2:
                    split = Split()
                    split.code = item[0]
                    split.time = hhmmss_to_time(item[1])
                    if self._more24 and len(item) >= 3 and item[2].isdigit():
                        split.days = int(item[2])
                    splits.append(split)
                else:
                    logging.error('In "{}" no code and no time'.format(row))
            self._splits = splits
        else:
            self._splits = splits
        return self._splits

    def show(self):
        splits = self._splits if self._splits is not None else []
        text = ''
        time_accuracy = race().get_setting('time_accuracy', 0)
        for split in splits:
            if self._more24:
                text += '{} {} {}\n'.format(split.code, split.time.to_str(time_accuracy), split.days)
            else:
                text += '{} {}\n'.format(split.code, split.time.to_str(time_accuracy))

        self._text.setText(text)

    @staticmethod
    def _get_example_text():
        return '31 12:45:00\n32 12:46:32\n33 12:49:12\n...'
