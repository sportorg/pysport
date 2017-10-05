import logging
import sys

from PyQt5.QtCore import QModelIndex
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QLineEdit, QApplication, QDialog, \
    QPushButton, QTimeEdit, QRadioButton, QSpinBox

from sportorg.app.controllers.global_access import GlobalAccess
from sportorg.app.models.memory import race, Organization, Result, find, ResultStatus
from sportorg.app.models.result_calculation import ResultCalculation
from sportorg.app.modules.utils.utils import datetime2qtime, qtime2datetime

from sportorg.language import _
from sportorg import config


class ResultEditDialog(QDialog):
    def __init__(self, table=None, index=None):
        super().__init__()
        self.init_ui()
        if table is not None:
            self.set_values_from_table(table, index)

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle(_('Result'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.setToolTip(_('Result Edit Window'))

        self.layout = QFormLayout(self)

        self.label_bib = QLabel(_('Bib'))
        self.item_bib = QSpinBox()
        self.item_bib.setMaximum(99999)
        self.item_bib.valueChanged.connect(self.show_person_info)
        self.layout.addRow(self.label_bib, self.item_bib)

        self.label_person_info = QLabel('')
        self.layout.addRow(self.label_person_info)

        self.label_finish = QLabel(_('Finish'))
        self.item_finish = QTimeEdit()
        self.item_finish.setDisplayFormat("hh:mm:ss")
        self.layout.addRow(self.label_finish, self.item_finish)

        self.label_start = QLabel(_('Start'))
        self.item_start = QTimeEdit()
        self.item_start.setDisplayFormat("hh:mm:ss")
        self.layout.addRow(self.label_start, self.item_start)

        self.label_result = QLabel(_('Result'))
        self.item_result = QLineEdit()
        self.item_result.setEnabled(False)
        self.layout.addRow(self.label_result, self.item_result)

        self.label_penalty = QLabel(_('Penalty'))
        self.item_penalty = QTimeEdit()
        self.item_penalty.setDisplayFormat("mm:ss")
        self.layout.addRow(self.label_penalty, self.item_penalty)

        self.radio_ok = QRadioButton(_('OK'))
        self.radio_ok.setChecked(True)
        self.radio_dns = QRadioButton(_('DNS'))
        self.radio_dnf = QRadioButton(_('DNF'))
        self.radio_overtime = QRadioButton(_('Overtime'))
        self.radio_dsq = QRadioButton(_('DSQ'))
        self.text_dsq = QLineEdit()

        self.layout.addRow(self.radio_ok)
        self.layout.addRow(self.radio_dns)
        self.layout.addRow(self.radio_dnf)
        self.layout.addRow(self.radio_overtime)
        self.layout.addRow(self.radio_dsq, self.text_dsq)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(e)
            self.close()

        self.button_ok = QPushButton(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

        self.show()

    def show_person_info(self):
        bib = self.item_bib.value()
        if bib:
            person = find(race().persons, bib=bib)
            if person:
                info = person.full_name
                if person.group:
                    info += '  ' + person.group.name
                self.label_person_info.setText(info)
            else:
                self.label_person_info.setText(_('not found'))

    def set_values_from_table(self, table, index):
        self.table = table
        self.current_index = index

        assert (isinstance(index, QModelIndex))
        orig_index_int = index.row()

        current_object = race().results[orig_index_int]
        assert (isinstance(current_object, Result))
        self.current_object = current_object

        if current_object.finish_time is not None:
            self.item_finish.setTime(datetime2qtime(current_object.finish_time))
        if current_object.start_time is not None:
            self.item_start.setTime(datetime2qtime(current_object.start_time))
        if current_object.result is not None:
            self.item_result.setText(str(current_object.get_result()))
        if current_object.penalty_time is not None:
            self.item_penalty.setTime(datetime2qtime(current_object.penalty_time))
        if current_object.person:
            self.item_bib.setValue(current_object.person.bib)

        if current_object.status == ResultStatus.OK or current_object.status == 0:
            self.radio_ok.setChecked(True)
        elif current_object.status == ResultStatus.DISQUALIFIED or current_object.status == 1:
            self.radio_dsq.setChecked(True)
        elif current_object.status == ResultStatus.OVERTIME or current_object.status == 2:
            self.radio_overtime.setChecked(True)
        elif current_object.status == ResultStatus.DID_NOT_FINISH or current_object.status == 7:
            self.radio_dnf.setChecked(True)
        elif current_object.status == ResultStatus.DID_NOT_START or current_object.status == 8:
            self.radio_dns.setChecked(True)

    def apply_changes_impl(self):
        changed = False
        result = self.current_object
        assert (isinstance(result, Result))

        time = qtime2datetime(self.item_finish.time())
        if result.finish_time != time:
            result.finish_time = time
            changed = True

        time = qtime2datetime(self.item_start.time())
        if result.start_time != time:
            result.start_time = time
            changed = True

        cur_bib = -1
        new_bib = self.item_bib.value()
        if result.person:
            cur_bib = result.person.bib

        if cur_bib != new_bib:
            new_person = find(race().persons, bib=new_bib)
            result.person = new_person
            GlobalAccess().get_result_table().model().init_cache()
            changed = True

        status = -1
        if self.radio_ok.isChecked():
            status = 0
        elif self.radio_dsq.isChecked():
            status = 1
        elif self.radio_overtime.isChecked():
            status = 2
        elif self.radio_dnf.isChecked():
            status = 7
        elif self.radio_dn8.isChecked():
            status = 8
        if result.status != status:
            result.status = status
            changed = True

        if changed:
            ResultCalculation().process_results()
            self.get_parent_window().refresh()

    def get_parent_window(self):
        return GlobalAccess().get_main_window()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ResultEditDialog()
    sys.exit(app.exec_())
