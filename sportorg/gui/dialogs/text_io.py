import logging

from PySide2 import QtCore, QtWidgets
from PySide2.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QVBoxLayout, QWidget

from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.memory import Qualification, ResultManual, race
from sportorg.utils.time import hhmmss_to_time, time_to_hhmmss


def get_value_options():
    return [
        translate('Start'),
        translate('Finish'),
        translate('Result'),
        translate('Credit'),
        translate('Penalty time'),
        translate('Penalty legs'),
        translate('Card number'),
        translate('Group'),
        translate('Team'),
        translate('Qualification'),
        translate('Bib'),
        translate('Comment'),
    ]


def get_readonly_options():
    return [translate('Result')]


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

        self.separator_grid_layout = QtWidgets.QGridLayout(self.separator_group_box)

        self.space_radio_button = QtWidgets.QRadioButton(self.separator_group_box)
        self.separator_grid_layout.addWidget(self.space_radio_button, 0, 0, 1, 1)

        self.tab_radio_button = QtWidgets.QRadioButton(self.separator_group_box)
        self.tab_radio_button.setChecked(True)
        self.separator_grid_layout.addWidget(self.tab_radio_button, 1, 0, 1, 1)

        self.semicolon_radio_button = QtWidgets.QRadioButton(self.separator_group_box)
        self.separator_grid_layout.addWidget(self.semicolon_radio_button, 2, 0, 1, 1)

        self.custom_layout = QtWidgets.QHBoxLayout()

        self.custom_radio_button = QtWidgets.QRadioButton(self.separator_group_box)

        self.custom_layout.addWidget(self.custom_radio_button)
        self.custom_edit = QtWidgets.QLineEdit(self.separator_group_box)

        self.custom_layout.addWidget(self.custom_edit)
        self.separator_grid_layout.addLayout(self.custom_layout, 3, 0, 1, 1)
        self.grid_layout.addWidget(self.separator_group_box, 0, 1, 1, 1)

        self.options_group_box = QtWidgets.QGroupBox(self)
        self.options_grid_layout = QtWidgets.QGridLayout(self.options_group_box)
        self.option_creating_new_result_checkbox = QCheckBox(
            translate("Create new result, if doesn't exist")
        )
        self.options_grid_layout.addWidget(
            self.option_creating_new_result_checkbox, 0, 0, 1, 1
        )
        self.grid_layout.addWidget(self.options_group_box, 1, 0, 1, 2)

        self.text_edit = QtWidgets.QPlainTextEdit(self)
        self.grid_layout.addWidget(self.text_edit, 2, 0, 1, 2)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(translate('OK'))
        self.button_ok.clicked.connect(self.accept)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate('Cancel'))
        self.button_cancel.clicked.connect(self.reject)

        self.layout.addWidget(widget)
        self.layout.addWidget(button_box)

        self.retranslate_ui(self)

    def save_to_file(self):
        pass

    def load_from_file(self):
        pass

    def retranslate_ui(self, text_io):
        text_io.setWindowTitle(translate('Dialog'))
        self.value_group_box.setTitle(translate('Values'))
        self.id_label.setText(translate('Identifier'))
        self.bib_radio_button.setText(translate('Bib'))
        self.name_radio_button.setText(translate('Person name'))
        self.value_label.setText(translate('Value'))
        self.separator_group_box.setTitle(translate('Separator'))
        self.space_radio_button.setText(translate('space'))
        self.tab_radio_button.setText(translate('tab'))
        self.semicolon_radio_button.setText(translate('semicolon'))
        self.custom_radio_button.setText(translate('custom'))
        self.options_group_box.setTitle(translate('Options'))
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

            readonly = key in get_readonly_options()

            if readonly:
                self.button_ok.setDisabled(True)
            else:
                self.button_ok.setDisabled(False)

            if key == translate('Finish'):
                self.option_creating_new_result_checkbox.setDisabled(False)
            else:
                self.option_creating_new_result_checkbox.setDisabled(True)

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

    def accept(self, *args, **kwargs):
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
                            set_property(
                                person,
                                key,
                                value,
                                creating_new_result=self.option_creating_new_result_checkbox.isChecked(),
                            )
                            success_count += 1
                        else:
                            logging.debug('text_io: no person found for line ' + i)
                    else:
                        logging.debug('text_io: empty value for line ' + i)
            logging.debug(
                'text_io: processed '
                + str(success_count)
                + ' from '
                + str(len(lines))
                + ' lines'
            )
        except Exception as e:
            logging.error(e)

        super().accept(*args, **kwargs)


def get_text(key, value, separator):
    ret = []
    for i in race().persons:
        id_str = get_id(i, key)
        if id_str:
            value_str = get_property(i, value)
            if not value_str:
                value_str = ''
            ret.append(id_str + separator + value_str)
    return '\n'.join(ret)


def get_id(person, index):
    if index == 'bib':
        return str(person.bib)
    elif index == 'person name':
        return person.full_name

    return ''


def get_person_by_id(index, value):
    for i in race().persons:
        if index == 'bib':
            if i.bib == int(value):
                return i
        elif index == 'person name':
            if i.full_name == value:
                return i
    return None


def get_property(person, key):
    if key == translate('Start'):
        result = race().find_person_result(person)
        if result:
            return time_to_hhmmss(result.get_start_time())
        else:
            return time_to_hhmmss(person.start_time)
    elif key == translate('Finish'):
        result = race().find_person_result(person)
        if result:
            return time_to_hhmmss(result.get_finish_time())
    elif key == translate('Result'):
        result = race().find_person_result(person)
        if result:
            return result.get_result()
    elif key == translate('Credit'):
        result = race().find_person_result(person)
        if result:
            return time_to_hhmmss(result.get_credit_time())
        else:
            return '00:00:00'
    elif key == translate('Penalty time'):
        result = race().find_person_result(person)
        if result:
            return time_to_hhmmss(result.get_penalty_time())
        else:
            return '00:00:00'
    elif key == translate('Penalty legs'):
        result = race().find_person_result(person)
        if result and result.penalty_laps:
            return str(result.penalty_laps)
    elif key == translate('Card number'):
        if person.card_number:
            return str(person.card_number)
    elif key == translate('Group'):
        if person.group:
            return person.group.name
    elif key == translate('Team'):
        if person.organization:
            return person.organization.name
    elif key == translate('Qualification'):
        return person.qual.get_title()
    elif key == translate('Bib'):
        return str(person.bib)
    elif key == translate('Comment'):
        return str(person.comment)

    return ''


def set_property(person, key, value, **options):
    if key == translate('Start'):
        result = race().find_person_result(person)
        if result:
            result.start_time = hhmmss_to_time(value)
            person.start_time = hhmmss_to_time(value)
        else:
            person.start_time = hhmmss_to_time(value)
    elif key == translate('Finish'):
        result = race().find_person_result(person)
        if result:
            result.finish_time = hhmmss_to_time(value)
        elif options.get('creating_new_result', False):
            result = race().new_result(ResultManual)
            result.person = person
            result.bib = person.bib
            result.finish_time = hhmmss_to_time(value)
            race().add_new_result(result)
    elif key == translate('Result'):
        pass
    elif key == translate('Credit'):
        result = race().find_person_result(person)
        if result:
            result.credit_time = hhmmss_to_time(value)
    elif key == translate('Penalty time'):
        result = race().find_person_result(person)
        if result:
            result.penalty_time = hhmmss_to_time(value)
    elif key == translate('Penalty legs'):
        result = race().find_person_result(person)
        if result:
            result.penalty_laps = int(value)
    elif key == translate('Card number'):
        race().person_card_number(person, int(value))
    elif key == translate('Group'):
        group = race().find_group(value)
        if group:
            person.group = group
    elif key == translate('Team'):
        team = race().find_team(value)
        if team:
            person.organization = team
    elif key == translate('Qualification'):
        qual = Qualification.get_qual_by_name(value)
        if qual:
            person.qual = qual
    elif key == translate('Bib'):
        if value.isdigit():
            new_bib = int(value)
            person.bib = new_bib
    elif key == translate('Comment'):
        person.comment = value
