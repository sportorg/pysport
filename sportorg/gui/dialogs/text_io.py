import logging

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QWidget

from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.memory import race, Person, Qualification
from sportorg.utils.time import time_to_hhmmss, hhmmss_to_time


def get_value_options():
    return [_('Start'), _('Finish'), _('Result'), _('Credit'), _('Penalty time'), _('Penalty legs'), _('Card number'),
            _('Group'), _('Team'), _('Qualification'), _('Bib')]


class TextExchangeDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.resize(319, 462)
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QVBoxLayout(self)

        self.grid_layout = QtWidgets.QGridLayout()
        widget = QWidget(self)
        widget.setLayout(self.grid_layout)

        self.value_group_box = QtWidgets.QGroupBox(self)

        self.grid_layout_child = QtWidgets.QGridLayout(self.value_group_box)

        self.id_label = QtWidgets.QLabel(self.value_group_box)

        self.grid_layout_child.addWidget(self.id_label, 0, 0, 1, 1)
        self.id_layout = QtWidgets.QVBoxLayout()

        self.bib_radio_button = QtWidgets.QRadioButton(self.value_group_box)
        self.bib_radio_button.setChecked(True)

        self.id_layout.addWidget(self.bib_radio_button)
        self.name_radio_button = QtWidgets.QRadioButton(self.value_group_box)

        self.id_layout.addWidget(self.name_radio_button)
        self.grid_layout_child.addLayout(self.id_layout, 0, 1, 1, 1)
        self.value_label = QtWidgets.QLabel(self.value_group_box)

        self.grid_layout_child.addWidget(self.value_label, 1, 0, 1, 1)
        self.value_combo_box = QtWidgets.QComboBox(self.value_group_box)

        self.value_combo_box.addItems(get_value_options())
        self.grid_layout_child.addWidget(self.value_combo_box, 1, 1, 1, 1)
        self.id_label.raise_()
        self.bib_radio_button.raise_()
        self.value_label.raise_()
        self.value_combo_box.raise_()
        self.grid_layout.addWidget(self.value_group_box, 0, 0, 1, 1)
        self.separator_group_box = QtWidgets.QGroupBox(self)

        self.gridLayout = QtWidgets.QGridLayout(self.separator_group_box)

        self.space_radio_button = QtWidgets.QRadioButton(self.separator_group_box)
        self.gridLayout.addWidget(self.space_radio_button, 0, 0, 1, 1)

        self.tab_radio_button = QtWidgets.QRadioButton(self.separator_group_box)
        self.tab_radio_button.setChecked(True)
        self.gridLayout.addWidget(self.tab_radio_button, 1, 0, 1, 1)

        self.semicolon_radio_button = QtWidgets.QRadioButton(self.separator_group_box)
        self.gridLayout.addWidget(self.semicolon_radio_button, 2, 0, 1, 1)

        self.custom_layout = QtWidgets.QHBoxLayout()

        self.custom_radio_button = QtWidgets.QRadioButton(self.separator_group_box)

        self.custom_layout.addWidget(self.custom_radio_button)
        self.custom_edit = QtWidgets.QLineEdit(self.separator_group_box)

        self.custom_layout.addWidget(self.custom_edit)
        self.gridLayout.addLayout(self.custom_layout, 3, 0, 1, 1)
        self.grid_layout.addWidget(self.separator_group_box, 0, 1, 1, 1)

        self.text_edit = QtWidgets.QPlainTextEdit(self)
        self.grid_layout.addWidget(self.text_edit, 1, 0, 1, 2)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(_('OK'))
        self.button_ok.clicked.connect(self.accept)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(_('Cancel'))
        self.button_cancel.clicked.connect(self.reject)

        self.layout.addWidget(widget)
        self.layout.addWidget(button_box)

        self.retranslate_ui(self)

    def retranslate_ui(self, text_io):
        text_io.setWindowTitle(_("Dialog"))
        self.value_group_box.setTitle(_("Values"))
        self.id_label.setText(_("Identifier"))
        self.bib_radio_button.setText(_("Bib"))
        self.name_radio_button.setText(_("Person name"))
        self.value_label.setText(_("Value"))
        self.separator_group_box.setTitle(_("Separator"))
        self.space_radio_button.setText(_("space"))
        self.tab_radio_button.setText(_("tab"))
        self.semicolon_radio_button.setText(_("semicolon"))
        self.custom_radio_button.setText(_("custom"))
        self.text_edit.setPlainText('')

        self.get_text_wrapper()

        self.value_combo_box.currentIndexChanged.connect(self.get_text_wrapper)
        self.bib_radio_button.clicked.connect(self.get_text_wrapper)
        self.name_radio_button.clicked.connect(self.get_text_wrapper)
        self.space_radio_button.clicked.connect(self.get_text_wrapper)
        self.semicolon_radio_button.clicked.connect(self.get_text_wrapper)
        self.tab_radio_button.clicked.connect(self.get_text_wrapper)
        self.custom_radio_button.clicked.connect(self.get_text_wrapper)
        self.custom_edit.textChanged.connect(self.get_text_wrapper)

    def get_text_wrapper(self):
        try:
            index = 'bib'
            if self.name_radio_button.isChecked():
                index = 'person name'

            key = self.value_combo_box.currentText()

            separator = ' '
            if self.tab_radio_button.isChecked():
                separator = '\t'
            elif self.semicolon_radio_button.isChecked():
                separator = ';'
            elif self.custom_radio_button.isChecked():
                separator = self.custom_edit.text()

            self.text_edit.setPlainText(get_text(index, key, separator))
        except Exception as e:
            logging.error(e)

    def accept(self):
        try:
            index_type = 'bib'
            if self.name_radio_button.isChecked():
                index_type = 'person name'

            key = self.value_combo_box.currentText()

            separator = ' '
            if self.tab_radio_button.isChecked():
                separator = '\t'
            elif self.semicolon_radio_button.isChecked():
                separator = ';'
            elif self.custom_radio_button.isChecked():
                separator = self.custom_edit.text()

            text = self.text_edit.toPlainText()
            lines = text.split('\n')
            success_count = 0
            for i in lines:
                arr = i.split(separator)
                if len(arr) > 1:
                    value = arr[-1]
                    index = arr[0]
                    if separator == ' ' and len(arr) > 2:
                        if index_type == 'person name':
                            index += separator + arr[1]
                        value = ' '.join(arr[1:])

                    if value:
                        person = get_person_by_id(index_type, index)
                        if person:
                            set_property(person, key, value)
                            success_count += 1
                        else:
                            logging.debug('text_io: no person found for line ' + i)
                    else:
                        logging.debug('text_io: empty value for line ' + i)
            logging.debug('text_io: processed ' + str(success_count) + ' from ' + str(len(lines)) + ' lines')
        except Exception as e:
            logging.error(e)

        self.close()


def get_text(key, value, separator):
    ret = []
    for i in race().persons:
        assert isinstance(i, Person)
        id_str = get_id(i, key)
        if id_str:
            value_str = get_property(i, value)
            if not value_str:
                value_str = ''
            ret.append(id_str + separator + value_str)
    return '\n'.join(ret)


def get_id(person, index):
    assert isinstance(person, Person)
    if index == 'bib':
        return str(person.bib)
    elif index == 'person name':
        return person.full_name

    return ''


def get_person_by_id(index, value):
    for i in race().persons:
        assert isinstance(i, Person)
        if index == 'bib':
            if i.bib == int(value):
                return i
        elif index == 'person name':
            if i.full_name == value:
                return i
    return None


def get_property(person, key):
    assert isinstance(person, Person)

    if key == _('Start'):
        result = race().find_person_result(person)
        if result:
            return time_to_hhmmss(result.get_start_time())
        else:
            return time_to_hhmmss(person.start_time)
    elif key == _('Finish'):
        result = race().find_person_result(person)
        if result:
            return time_to_hhmmss(result.get_finish_time())
    elif key == _('Result'):
        result = race().find_person_result(person)
        if result:
            return result.get_result()
    elif key == _('Credit'):
        result = race().find_person_result(person)
        if result:
            return time_to_hhmmss(result.get_credit_time())
        else:
            return '00:00:00'
    elif key == _('Penalty time'):
        result = race().find_person_result(person)
        if result:
            return time_to_hhmmss(result.get_penalty_time())
        else:
            return '00:00:00'
    elif key == _('Penalty legs'):
        result = race().find_person_result(person)
        if result and result.penalty_laps:
            return str(result.penalty_laps)
    elif key == _('Card number'):
        if person.card_number:
            return str(person.card_number)
    elif key == _('Group'):
        if person.group:
            return person.group.name
    elif key == _('Team'):
        if person.organization:
            return person.organization.name
    elif key == _('Qualification'):
        return person.qual.get_title()
    elif key == _('Bib'):
        return str(person.bib)

    return ''


def set_property(person, key, value):
    assert isinstance(person, Person)
    if key == _('Start'):
        result = race().find_person_result(person)
        if result:
            result.start_time = hhmmss_to_time(value)
            person.start_time = hhmmss_to_time(value)
        else:
            person.start_time = hhmmss_to_time(value)
    elif key == _('Finish'):
        result = race().find_person_result(person)
        if result:
            result.finish_time = hhmmss_to_time(value)
    elif key == _('Result'):
        pass
    elif key == _('Credit'):
        result = race().find_person_result(person)
        if result:
            result.credit_time = hhmmss_to_time(value)
    elif key == _('Penalty time'):
        result = race().find_person_result(person)
        if result:
            result.penalty_time = hhmmss_to_time(value)
    elif key == _('Penalty legs'):
        result = race().find_person_result(person)
        if result:
            result.penalty_laps = int(value)
    elif key == _('Card number'):
        race().person_card_number(person, int(value))
    elif key == _('Group'):
        group = race().find_group(value)
        if(group):
            person.group = group
    elif key == _('Team'):
        team = race().find_team(value)
        if (team):
            person.organization = team
    elif key == _('Qualification'):
        qual = Qualification.get_qual_by_name(value)
        if (qual):
            person.qual = qual
    elif key == _('Bib'):
        if value.isdigit():
            new_bib = int(value)
            person.bib = new_bib
