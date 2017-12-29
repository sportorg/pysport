import logging

from abc import abstractmethod
from typing import List, Tuple

from PyQt5.QtCore import QModelIndex
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QLineEdit, QDialog, \
    QPushButton, QTimeEdit, QRadioButton, QSpinBox, QGroupBox, QScrollArea, QGridLayout, QTextEdit, QCheckBox, \
    QDialogButtonBox

from sportorg import config
from sportorg.core.otime import OTime
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.memory import race, Result, find, ResultStatus, Person, Limit, SystemType, Split
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.result_checker import ResultChecker, ResultCheckerException
from sportorg.utils.time import time_to_qtime, time_to_otime, hhmmss_to_time


class ResultEditDialog(QDialog):
    def __init__(self, table=None, index=None):
        super().__init__(GlobalAccess().get_main_window())
        if table is not None:
            self.table = table
            self.current_index = index
            assert (isinstance(self.current_index, QModelIndex))
            self.current_object = race().results[self.current_index.row()]
            assert (isinstance(self.current_object, Result))

    def exec(self):
        self.init_ui()
        self.set_values_from_table()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Result'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.item_sportident_card = QSpinBox()
        self.item_sportident_card.setMaximum(9999999)

        self.item_bib = QSpinBox()
        self.item_bib.setMaximum(Limit.BIB)
        self.item_bib.valueChanged.connect(self.show_person_info)

        self.label_person_info = QLabel('')

        self.item_finish = QTimeEdit()
        self.item_finish.setDisplayFormat("hh:mm:ss")

        self.item_start = QTimeEdit()
        self.item_start.setDisplayFormat("hh:mm:ss")

        self.item_result = QLineEdit()
        self.item_result.setEnabled(False)

        self.item_penalty = QTimeEdit()
        self.item_penalty.setDisplayFormat("hh:mm:ss")

        self.item_penalty_laps = QSpinBox()
        self.item_penalty_laps.setMaximum(1000000)

        self.radio_ok = QRadioButton(_('OK'))
        self.radio_ok.setChecked(True)
        self.radio_dns = QRadioButton(_('DNS'))
        self.radio_dnf = QRadioButton(_('DNF'))
        self.radio_overtime = QRadioButton(_('Overtime'))
        self.radio_dsq = QRadioButton(_('DSQ'))
        self.text_dsq = QLineEdit()

        self.splits = SplitsText()

        if self.current_object.system_type == SystemType.SPORTIDENT:
            self.layout.addRow(QLabel(_('Card')), self.item_sportident_card)
        self.layout.addRow(QLabel(_('Bib')), self.item_bib)
        self.layout.addRow(QLabel(''), self.label_person_info)
        self.layout.addRow(QLabel(_('Start')), self.item_start)
        self.layout.addRow(QLabel(_('Finish')), self.item_finish)
        self.layout.addRow(QLabel(_('Penalty')), self.item_penalty)
        self.layout.addRow(QLabel(_('Penalty legs')), self.item_penalty_laps)
        self.layout.addRow(QLabel(_('Result')), self.item_result)

        self.layout.addRow(self.radio_ok)
        self.layout.addRow(self.radio_dns)
        self.layout.addRow(self.radio_dnf)
        self.layout.addRow(self.radio_overtime)
        self.layout.addRow(self.radio_dsq, self.text_dsq)

        if self.current_object.system_type == SystemType.SPORTIDENT:
            start_source = race().get_setting('sportident_start_source', 'protocol')
            finish_source = race().get_setting('sportident_finish_source', 'station')
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
                logging.exception(str(e))
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

    def show_person_info(self):
        bib = self.item_bib.value()
        self.label_person_info.setText('')
        self.button_ok.setEnabled(True)
        if bib:
            person = find(race().persons, bib=bib)
            if person:
                info = person.full_name
                if person.group:
                    info = '{}\n{}: {}'.format(info, _('Group'), person.group.name)
                if person.sportident_card is not None:
                    info = '{}\n{}: {}'.format(info, _('Card'), person.sportident_card)
                self.label_person_info.setText(info)
            else:
                self.label_person_info.setText(_('not found'))
                self.button_ok.setDisabled(True)

    def set_values_from_table(self):
        if self.current_object.system_type == SystemType.SPORTIDENT:
            if self.current_object.sportident_card is not None:
                self.item_sportident_card.setValue(int(self.current_object.sportident_card))
            self.splits.splits(self.current_object.splits)
            self.splits.show()
        if self.current_object.finish_time is not None:
            self.item_finish.setTime(time_to_qtime(self.current_object.finish_time))
        if self.current_object.start_time is not None:
            self.item_start.setTime(time_to_qtime(self.current_object.start_time))
        if self.current_object.result is not None:
            self.item_result.setText(str(self.current_object.get_result()))
        if self.current_object.penalty_time is not None:
            self.item_penalty.setTime(time_to_qtime(self.current_object.penalty_time))
        if self.current_object.penalty_laps:
            self.item_penalty_laps.setValue(self.current_object.penalty_laps)
        if self.current_object.person:
            self.item_bib.setValue(self.current_object.person.bib)

        if self.current_object.status == ResultStatus.OK:
            self.radio_ok.setChecked(True)
        elif self.current_object.status == ResultStatus.DISQUALIFIED:
            self.radio_dsq.setChecked(True)
        elif self.current_object.status == ResultStatus.OVERTIME:
            self.radio_overtime.setChecked(True)
        elif self.current_object.status == ResultStatus.DID_NOT_FINISH:
            self.radio_dnf.setChecked(True)
        elif self.current_object.status == ResultStatus.DID_NOT_START:
            self.radio_dns.setChecked(True)

    def apply_changes_impl(self):
        result = self.current_object
        changed = False

        if result.system_type == SystemType.SPORTIDENT:
            if result.sportident_card is None or int(result.sportident_card) != self.item_sportident_card.value():
                result.sportident_card = race().new_sportident_card(self.item_sportident_card.value())
                changed = True

            new_splits = self.splits.splits()
            if len(result.splits) == len(new_splits):
                for i, split in enumerate(result.splits):
                    if split != new_splits[i]:
                        changed = True
                        break
            else:
                changed = True
            result.splits = new_splits

        time = time_to_otime(self.item_finish.time())
        if result.finish_time != time:
            result.finish_time = time
            changed = True

        time = time_to_otime(self.item_start.time())
        if result.start_time != time:
            result.start_time = time
            changed = True

        time = time_to_otime(self.item_penalty.time())
        if result.penalty_time != time:
            result.penalty_time = time
            changed = True

        if result.penalty_laps != self.item_penalty_laps.value():
            result.penalty_laps = self.item_penalty_laps.value()
            changed = True

        cur_bib = -1
        new_bib = self.item_bib.value()
        if result.person:
            cur_bib = result.person.bib

        recheck = False
        if new_bib == 0:
            if result.person and result.system_type == SystemType.SPORTIDENT:
                if result.person.sportident_card == result.sportident_card:
                    result.person.sportident_card = None
            result.person = None
            changed = True
        elif cur_bib != new_bib:
            new_person = find(race().persons, bib=new_bib)
            if new_person is not None:
                assert isinstance(new_person, Person)
                if result.person:
                    if result.system_type == SystemType.SPORTIDENT:
                        result.person.sportident_card = None
                recheck = True
                result.person = new_person
                if result.system_type == SystemType.SPORTIDENT:
                    result.person.sportident_card = result.sportident_card

                    logging.info('Old status {}'.format(result.status))
                    try:
                        ResultChecker.checking(result)
                    except ResultCheckerException as e:
                        logging.error(str(e))
                    logging.info('New status {}'.format(result.status))

            GlobalAccess().get_result_table().model().init_cache()
            changed = True

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
        if result.status != status and not recheck:
            result.status = status
            changed = True

        if changed:
            if result.system_type == SystemType.SPORTIDENT:
                result.clear()
            ResultCalculation().process_results()
            GlobalAccess().get_main_window().refresh()


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


class Splits(SplitsObject):
    def __init__(self, splits=None):
        self._splits = splits  # type: List[Split]
        self._scroll = QScrollArea()
        self._box = QGroupBox(_('Splits'))
        self._splits_layout = QGridLayout()
        self._splits_layout.setSpacing(0)
        self._add_index = QSpinBox()
        self._delete_index = QSpinBox()
        self._add_button = QPushButton(_('Add'))
        self._delete_button = QPushButton(_('Delete'))
        layout = QFormLayout()
        layout.addRow(self._splits_layout)
        layout.addRow(self._add_index, self._add_button)
        layout.addRow(self._delete_index, self._delete_button)
        self._box.setLayout(layout)
        self._scroll.setWidget(self._box)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFixedHeight(200)
        self._scroll.setMinimumWidth(250)
        self._splits_item = []  # type: List[Tuple[QLabel, QLineEdit, QTimeEdit]]

        self._add_button.clicked.connect(self._add)
        self._delete_button.clicked.connect(self._delete)

    @property
    def widget(self):
        return self._scroll

    def splits(self, splits=None):
        if splits is None:
            splits = []
            i = 0
            for item in self._splits_item:
                split = Split()
                split.time = time_to_otime(item[2].time())
                if item[1].text().strip().isdigit():
                    split.code = int(item[1].text().strip())
                else:
                    if self._splits is not None and len(self._splits) > i:
                        split.code = self._splits[i].code
                    logging.error('{} not number'.format(item[1].text()))
                splits.append(split)
                i += 1
            self._splits = splits
        else:
            self._splits = splits
        return self._splits

    def _add(self):
        if self._add_index.value():
            split = Split()
            split.time = OTime.now()
            self.splits().insert(self._add_index.value()-1, split)
            self.show()

    def _delete(self):
        if 0 < self._delete_index.value() <= len(self._splits):
            self.splits().pop(self._delete_index.value()-1)
            self.show()

    def _clear(self):
        for item in self._splits_item:
            for j, widget in enumerate(item):
                self._splits_layout.removeWidget(widget)
                widget.setParent(None)
        self._splits_item = []

    def show(self):
        self._clear()
        splits = self._splits if self._splits is not None else []
        for i, split in enumerate(splits):
            code = QLineEdit()
            code.setText(str(split.code))
            time = QTimeEdit()
            time.setDisplayFormat("hh:mm:ss")
            time.setTime(time_to_qtime(split.time))
            item = (QLabel(str(i+1)), code, time)
            for j, widget in enumerate(item):
                self._splits_layout.addWidget(widget, i, j)
            self._splits_item.insert(i, item)
        self._add_index.setMaximum(len(splits)+1)
        self._add_index.setValue(len(splits)+1)
        self._delete_index.setMaximum(len(splits))
        self._delete_index.setValue(0)
        if len(splits) == 0:
            self._delete_button.setDisabled(True)
        else:
            self._delete_button.setDisabled(False)


class SplitsText(SplitsObject):
    def __init__(self, splits=None):
        self._splits = splits
        self._box = QGroupBox(_('Splits'))
        self._layout = QFormLayout()
        self._text = QTextEdit()
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
                    split.time = hhmmss_to_time(item[1])
                    if item[0].isdigit():
                        split.code = int(item[0])
                    else:
                        logging.error('{} not number'.format(item[0]))
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
        for split in splits:
            text += '{} {}\n'.format(split.code, str(split.time))
        self._text.setText(text)

    @staticmethod
    def _get_example_text():
        return '31 12:45:00\n32 12:46:32\n33 12:49:12\n...'
