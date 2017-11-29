import logging
import sys
from typing import List, Tuple

from PyQt5.QtCore import QModelIndex
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QLineEdit, QApplication, QDialog, \
    QPushButton, QTimeEdit, QRadioButton, QSpinBox, QGroupBox, QScrollArea, QGridLayout

from sportorg import config
from sportorg.core.otime import OTime
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.memory import race, Result, find, ResultStatus, Person, Limit, SystemType
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.result_checker import ResultChecker
from sportorg.utils.time import time_to_qtime, time_to_otime


class Punches:
    def __init__(self, punches=None):
        self._punches = punches  # type: List[Tuple[int, OTime]]
        self._scroll = QScrollArea()
        self._box = QGroupBox(_('Punches'))
        self._punches_layout = QGridLayout()
        self._punches_layout.setSpacing(0)
        self._add_index = QSpinBox()
        self._delete_index = QSpinBox()
        self._add_button = QPushButton(_('Add'))
        self._delete_button = QPushButton(_('Delete'))
        layout = QFormLayout()
        layout.addRow(self._punches_layout)
        layout.addRow(self._add_index, self._add_button)
        layout.addRow(self._delete_index, self._delete_button)
        self._box.setLayout(layout)
        self._scroll.setWidget(self._box)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFixedHeight(200)
        self._scroll.setMinimumWidth(250)
        self._punches_item = []  # type: List[Tuple[QLabel, QLineEdit, QTimeEdit]]

        self._add_button.clicked.connect(self._add)
        self._delete_button.clicked.connect(self._delete)

    @property
    def widget(self):
        return self._scroll

    def punches(self, punches=None):
        if punches is None:
            self._punches = []
            for item in self._punches_item:
                self._punches.append((
                    int(item[1].text()),
                    time_to_otime(item[2].time())
                ))

            return self._punches
        else:
            self._punches = punches

    def _add(self):
        if self._add_index.value():
            self._punches.insert(self._add_index.value()-1, (0, OTime.now()))
            self.show()

    def _delete(self):
        if 0 < self._delete_index.value() <= len(self._punches):
            self._punches.pop(self._delete_index.value()-1)
            self.show()

    def _clear(self):
        for item in self._punches_item:
            for j, widget in enumerate(item):
                self._punches_layout.removeWidget(widget)
                widget.setParent(None)
        self._punches_item = []

    def show(self):
        self._clear()
        punches = self._punches if self._punches is not None else []
        for i, p in enumerate(punches):
            code = QLineEdit()
            code.setText(str(p[0]))
            time = QTimeEdit()
            time.setDisplayFormat("hh:mm:ss")
            time.setTime(time_to_qtime(p[1]))
            item = (QLabel(str(i+1)), code, time)
            for j, widget in enumerate(item):
                self._punches_layout.addWidget(widget, i, j)
            self._punches_item.insert(i, item)
        self._add_index.setMaximum(len(punches)+1)
        self._add_index.setValue(len(punches)+1)
        self._delete_index.setMaximum(len(punches))
        self._delete_index.setValue(0)
        if len(punches) == 0:
            self._delete_button.setDisabled(True)
        else:
            self._delete_button.setDisabled(False)


class ResultEditDialog(QDialog):
    def __init__(self, table=None, index=None):
        super().__init__()
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

    def close_dialog(self):
        self.close()

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
        self.item_penalty.setDisplayFormat("mm:ss")

        self.radio_ok = QRadioButton(_('OK'))
        self.radio_ok.setChecked(True)
        self.radio_dns = QRadioButton(_('DNS'))
        self.radio_dnf = QRadioButton(_('DNF'))
        self.radio_overtime = QRadioButton(_('Overtime'))
        self.radio_dsq = QRadioButton(_('DSQ'))
        self.text_dsq = QLineEdit()

        self.punches = Punches()

        if self.current_object.system_type == SystemType.SPORTIDENT:
            self.layout.addRow(QLabel(_('Card')), self.item_sportident_card)
        self.layout.addRow(QLabel(_('Bib')), self.item_bib)
        self.layout.addRow(QLabel(''), self.label_person_info)
        self.layout.addRow(QLabel(_('Finish')), self.item_finish)
        self.layout.addRow(QLabel(_('Start')), self.item_start)
        self.layout.addRow(QLabel(_('Result')), self.item_result)
        self.layout.addRow(QLabel(_('Penalty')), self.item_penalty)

        self.layout.addRow(self.radio_ok)
        self.layout.addRow(self.radio_dns)
        self.layout.addRow(self.radio_dnf)
        self.layout.addRow(self.radio_overtime)
        self.layout.addRow(self.radio_dsq, self.text_dsq)

        if self.current_object.system_type == SystemType.SPORTIDENT:
            self.layout.addRow(self.punches.widget)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(str(e))
            self.close()

        self.button_ok = QPushButton(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

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
            self.punches.punches(self.current_object.punches)
            self.punches.show()
        if self.current_object.finish_time is not None:
            self.item_finish.setTime(time_to_qtime(self.current_object.finish_time))
        if self.current_object.start_time is not None:
            self.item_start.setTime(time_to_qtime(self.current_object.start_time))
        if self.current_object.result is not None:
            self.item_result.setText(str(self.current_object.get_result()))
        if self.current_object.penalty_time is not None:
            self.item_penalty.setTime(time_to_qtime(self.current_object.penalty_time))
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

            result.punches = self.punches.punches()
            changed = True

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

        cur_bib = -1
        new_bib = self.item_bib.value()
        if result.person:
            cur_bib = result.person.bib

        recheck = False
        if new_bib == 0:
            if result.person:
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
                    ResultChecker.checking(result)
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
            ResultCalculation().process_results()
            GlobalAccess().get_main_window().refresh()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ResultEditDialog()
    sys.exit(app.exec_())
