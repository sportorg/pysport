import logging
from datetime import date

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QFormLayout, QLabel, QLineEdit, QSpinBox, QTimeEdit, QTextEdit, QCheckBox, QDialog, \
    QDialogButtonBox, QDateEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.constant import get_names, get_race_groups, get_race_teams
from sportorg.models.memory import race, Person, find, Qualification, Limit, Organization
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.modules.configs.configs import Config
from sportorg.modules.teamwork import Teamwork
from sportorg.utils.time import time_to_qtime, time_to_otime, qdate_to_date


class PersonEditDialog(QDialog):
    GROUP_NAME = ''
    ORGANIZATION_NAME = ''

    def __init__(self, person, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        self.is_ok = {}
        assert (isinstance(person, Person))
        self.current_object = person
        self.is_new = is_new

        self.time_format = 'hh:mm:ss'
        time_accuracy = race().get_setting('time_accuracy', 0)
        if time_accuracy:
            self.time_format = 'hh:mm:ss.zzz'

    def exec_(self):
        self.init_ui()
        self.set_values_from_model()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_('Entry properties'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)
        self.label_surname = QLabel(_('Last name'))
        self.item_surname = QLineEdit()
        self.layout.addRow(self.label_surname, self.item_surname)

        self.label_name = QLabel(_('First name'))
        self.item_name = AdvComboBox()
        self.item_name.addItems(get_names())
        self.layout.addRow(self.label_name, self.item_name)

        self.label_group = QLabel(_('Group'))
        self.item_group = AdvComboBox()
        self.item_group.addItems(get_race_groups())
        self.layout.addRow(self.label_group, self.item_group)

        self.label_team = QLabel(_('Team'))
        self.item_team = AdvComboBox()
        self.item_team.addItems(get_race_teams())
        self.layout.addRow(self.label_team, self.item_team)

        use_birthday = Config().configuration.get('use_birthday', False)
        if use_birthday:
            self.label_birthday = QLabel(_('Birthday'))
            self.item_birthday = QDateEdit()
            self.item_birthday.setDate(date.today())
            self.item_birthday.setMaximumDate(date.today())
            self.layout.addRow(self.label_birthday, self.item_birthday)
        else:
            self.label_year = QLabel(_('Year of birth'))
            self.item_year = QSpinBox()
            self.item_year.setMinimum(0)
            self.item_year.setMaximum(date.today().year)
            self.item_year.editingFinished.connect(self.year_change)
            self.layout.addRow(self.label_year, self.item_year)

        self.label_qual = QLabel(_('Qualification'))
        self.item_qual = AdvComboBox()
        for i in list(Qualification):
            self.item_qual.addItem(i.get_title())
        self.layout.addRow(self.label_qual, self.item_qual)

        self.is_ok['bib'] = True
        self.label_bib = QLabel(_('Bib'))
        self.item_bib = QSpinBox()
        self.item_bib.setMinimum(0)
        self.item_bib.setMaximum(Limit.BIB)
        self.item_bib.valueChanged.connect(self.check_bib)
        self.layout.addRow(self.label_bib, self.item_bib)

        self.label_bib_info = QLabel('')
        self.layout.addRow(QLabel(''), self.label_bib_info)

        self.label_start = QLabel(_('Start time'))
        self.item_start = QTimeEdit()
        self.item_start.setDisplayFormat(self.time_format)
        self.layout.addRow(self.label_start, self.item_start)

        self.label_start_group = QLabel(_('Start group'))
        self.item_start_group = QSpinBox()
        self.item_start_group.setMinimum(0)
        self.item_start_group.setMaximum(99)
        self.layout.addRow(self.label_start_group, self.item_start_group)

        self.is_ok['card'] = True
        self.label_card = QLabel(_('Punch card #'))
        self.item_card = QSpinBox()
        self.item_card.setMinimum(0)
        self.item_card.setMaximum(9999999)
        self.item_card.valueChanged.connect(self.check_card)
        self.layout.addRow(self.label_card, self.item_card)

        self.label_card_info = QLabel('')
        self.layout.addRow(QLabel(''), self.label_card_info)

        self.item_rented = QCheckBox(_('rented card'))
        self.item_paid = QCheckBox(_('is paid'))
        self.item_out_of_competition = QCheckBox(_('out of competition'))
        self.item_personal = QCheckBox(_('personal participation'))
        self.layout.addRow(self.item_rented, self.item_out_of_competition)
        self.layout.addRow(self.item_paid, self.item_personal)

        self.label_comment = QLabel(_('Comment'))
        self.item_comment = QTextEdit()
        self.item_comment.setTabChangesFocus(True)
        self.layout.addRow(self.label_comment, self.item_comment)

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

    def year_change(self):
        """
        Convert 2 digits of year to 4
        2 -> 2002
        11 - > 2011
        33 -> 1933
        56 -> 1956
        98 - > 1998
        0 -> 0 exception!
        """
        widget = self.sender()
        assert isinstance(widget, QSpinBox)
        year = widget.value()
        if 0 < year < 100:
            cur_year = date.today().year
            new_year = cur_year - cur_year % 100 + year
            if new_year > cur_year:
                new_year -= 100
            widget.setValue(new_year)

    def items_ok(self):
        ret = True
        for item_name in self.is_ok.keys():
            if self.is_ok[item_name] is not True:
                ret = False
                break
        return ret

    def check_bib(self):
        bib = self.item_bib.value()
        self.label_bib_info.setText('')
        if bib:
            person = find(race().persons, bib=bib)
            if person:
                if person.bib == self.current_object.bib:
                    self.button_ok.setEnabled(True)
                    return
                self.button_ok.setDisabled(True)
                self.is_ok['bib'] = False
                info = '{}\n{}'.format(_('Number already exists'), person.full_name)
                if person.group:
                    info = '{}\n{}: {}'.format(info, _('Group'), person.group.name)
                self.label_bib_info.setText(info)
            else:
                self.label_bib_info.setText(_('Number is unique'))
                self.is_ok['bib'] = True
                if self.items_ok():
                    self.button_ok.setEnabled(True)
        else:
            self.button_ok.setEnabled(True)

    def check_card(self):
        number = self.item_card.value()
        self.label_card_info.setText('')
        if number:
            person = None
            for _p in race().persons:
                if _p.card_number and _p.card_number == number:
                    person = _p
                    break
            if person:
                if person.card_number == self.current_object.card_number:
                    self.button_ok.setEnabled(True)
                    return
                self.button_ok.setDisabled(True)
                self.is_ok['card'] = False
                info = '{}\n{}'.format(_('Card number already exists'), person.full_name)
                if person.group:
                    info = '{}\n{}: {}'.format(info, _('Group'), person.group.name)
                if person.bib:
                    info = '{}\n{}: {}'.format(info, _('Bib'), person.bib)
                self.label_card_info.setText(info)
            else:
                self.label_card_info.setText(_('Card number is unique'))
                self.is_ok['card'] = True
                if self.items_ok():
                    self.button_ok.setEnabled(True)
        else:
            self.button_ok.setEnabled(True)

    def set_values_from_model(self):
        self.item_surname.setText(self.current_object.surname)
        self.item_surname.selectAll()
        self.item_name.setCurrentText(self.current_object.name)
        if self.current_object.group is not None:
            self.item_group.setCurrentText(self.current_object.group.name)
        else:
            self.item_group.setCurrentText(self.GROUP_NAME)
        if self.current_object.organization is not None:
            self.item_team.setCurrentText(self.current_object.organization.name)
        else:
            self.item_team.setCurrentText(self.ORGANIZATION_NAME)
        if self.current_object.qual:
            self.item_qual.setCurrentText(self.current_object.qual.get_title())
        if self.current_object.bib:
            self.item_bib.setValue(int(self.current_object.bib))
        if self.current_object.start_time is not None:
            time = time_to_qtime(self.current_object.start_time)
            self.item_start.setTime(time)
        if self.current_object.start_group is not None:
            self.item_start_group.setValue(int(self.current_object.start_group))

        if self.current_object.card_number:
            self.item_card.setValue(self.current_object.card_number)

        self.item_out_of_competition.setChecked(self.current_object.is_out_of_competition)
        self.item_paid.setChecked(self.current_object.is_paid)
        self.item_paid.setChecked(self.current_object.is_paid)
        self.item_personal.setChecked(self.current_object.is_personal)
        self.item_rented.setChecked(self.current_object.is_rented_card)

        self.item_comment.setText(self.current_object.comment)

        use_birthday = Config().configuration.get('use_birthday', False)
        if use_birthday:
            if self.current_object.birth_date:
                self.item_birthday.setDate(self.current_object.birth_date)
        else:
            if self.current_object.get_year():
                self.item_year.setValue(self.current_object.get_year())

    def apply_changes_impl(self):
        person = self.current_object
        assert (isinstance(person, Person))
        if self.is_new:
            race().persons.insert(0, person)
        if person.name != self.item_name.currentText():
            person.name = self.item_name.currentText()
        if person.surname != self.item_surname.text():
            person.surname = self.item_surname.text()
        if (person.group is not None and person.group.name != self.item_group.currentText()) or\
                (person.group is None and len(self.item_group.currentText()) > 0):
            person.group = find(race().groups, name=self.item_group.currentText())
        if (person.organization is not None and person.organization.name != self.item_team.currentText()) or \
                (person.organization is None and len(self.item_team.currentText()) > 0):
            organization = find(race().organizations, name=self.item_team.currentText())
            if organization is None:
                organization = Organization()
                organization.name = self.item_team.currentText()
                organization.generate_cache()
                race().organizations.append(organization)
                Teamwork().send(organization.to_dict())
            person.organization = organization
        if person.qual.get_title() != self.item_qual.currentText():
            person.qual = Qualification.get_qual_by_name(self.item_qual.currentText())
        if person.bib != self.item_bib.value():
            person.bib = self.item_bib.value()

        new_time = time_to_otime(self.item_start.time())
        if person.start_time != new_time:
            person.start_time = new_time

        if person.start_group != self.item_start_group.value() and self.item_start_group.value():
            person.start_group = self.item_start_group.value()

        if (not person.card_number or int(person.card_number) != self.item_card.value()) \
                and self.item_card.value:
            race().person_card_number(person, self.item_card.value())

        if person.is_out_of_competition != self.item_out_of_competition.isChecked():
            person.is_out_of_competition = self.item_out_of_competition.isChecked()

        if person.is_paid != self.item_paid.isChecked():
            person.is_paid = self.item_paid.isChecked()

        if person.is_rented_card != self.item_rented.isChecked():
            person.is_rented_card = self.item_rented.isChecked()

        if person.is_personal != self.item_personal.isChecked():
            person.is_personal = self.item_personal.isChecked()

        if person.comment != self.item_comment.toPlainText():
            person.comment = self.item_comment.toPlainText()

        use_birthday = Config().configuration.get('use_birthday', False)
        if use_birthday:
            new_birthday = qdate_to_date(self.item_birthday.date())
            if person.birth_date != new_birthday and new_birthday:
                if person.birth_date or new_birthday != date.today():
                    person.birth_date = new_birthday
        else:
            if person.get_year() != self.item_year.value():
                person.set_year(self.item_year.value())

        person.generate_cache()
        ResultCalculation(race()).process_results()
        Teamwork().send(person.to_dict())
