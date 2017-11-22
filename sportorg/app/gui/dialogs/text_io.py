import sys

import logging
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog

from sportorg.app.models.memory import race, Person
from sportorg.app.modules.utils.utils import time_to_hhmmss, hhmmss_to_time
from sportorg.language import _


def get_value_options():
    return [_('Start'), _('Finish'), _('Result'), _('Penalty time'), _('Penalty legs'), _('Card number'),
            _('Group'), _('Team'), _('Qualification')]

class TextExchangeDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.setObjectName("text_io")
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.resize(319, 462)
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.gridLayout_3 = QtWidgets.QGridLayout(self)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.value_group_box = QtWidgets.QGroupBox(self)
        self.value_group_box.setObjectName("value_group_box")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.value_group_box)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.id_label = QtWidgets.QLabel(self.value_group_box)
        self.id_label.setObjectName("id_label")
        self.gridLayout_2.addWidget(self.id_label, 0, 0, 1, 1)
        self.id_layout = QtWidgets.QVBoxLayout()
        self.id_layout.setObjectName("id_layout")
        self.bib_radio_button = QtWidgets.QRadioButton(self.value_group_box)
        self.bib_radio_button.setChecked(True)
        self.bib_radio_button.setObjectName("bib_radio_button")
        self.id_layout.addWidget(self.bib_radio_button)
        self.name_radio_button = QtWidgets.QRadioButton(self.value_group_box)
        self.name_radio_button.setObjectName("name_radio_button")
        self.id_layout.addWidget(self.name_radio_button)
        self.gridLayout_2.addLayout(self.id_layout, 0, 1, 1, 1)
        self.value_label = QtWidgets.QLabel(self.value_group_box)
        self.value_label.setObjectName("value_label")
        self.gridLayout_2.addWidget(self.value_label, 1, 0, 1, 1)
        self.value_combo_box = QtWidgets.QComboBox(self.value_group_box)
        self.value_combo_box.setObjectName("value_combo_box")
        self.value_combo_box.addItems(get_value_options())
        self.gridLayout_2.addWidget(self.value_combo_box, 1, 1, 1, 1)
        self.id_label.raise_()
        self.bib_radio_button.raise_()
        self.value_label.raise_()
        self.value_combo_box.raise_()
        self.gridLayout_3.addWidget(self.value_group_box, 0, 0, 1, 1)
        self.separator_group_box = QtWidgets.QGroupBox(self)
        self.separator_group_box.setObjectName("separator_group_box")
        self.gridLayout = QtWidgets.QGridLayout(self.separator_group_box)
        self.gridLayout.setObjectName("gridLayout")
        self.space_radio_button = QtWidgets.QRadioButton(self.separator_group_box)
        self.space_radio_button.setChecked(True)
        self.space_radio_button.setObjectName("space_radio_button")
        self.gridLayout.addWidget(self.space_radio_button, 0, 0, 1, 1)
        self.tab_radio_button = QtWidgets.QRadioButton(self.separator_group_box)
        self.tab_radio_button.setObjectName("tab_radio_button")
        self.gridLayout.addWidget(self.tab_radio_button, 1, 0, 1, 1)
        self.semicolon_radio_button = QtWidgets.QRadioButton(self.separator_group_box)
        self.semicolon_radio_button.setObjectName("semicolon_radio_button")
        self.gridLayout.addWidget(self.semicolon_radio_button, 2, 0, 1, 1)
        self.custom_layout = QtWidgets.QHBoxLayout()
        self.custom_layout.setObjectName("custom_layout")
        self.custom_radio_button = QtWidgets.QRadioButton(self.separator_group_box)
        self.custom_radio_button.setObjectName("custom_radio_button")
        self.custom_layout.addWidget(self.custom_radio_button)
        self.custom_edit = QtWidgets.QLineEdit(self.separator_group_box)
        self.custom_edit.setObjectName("custom_edit")
        self.custom_layout.addWidget(self.custom_edit)
        self.gridLayout.addLayout(self.custom_layout, 3, 0, 1, 1)
        self.gridLayout_3.addWidget(self.separator_group_box, 0, 1, 1, 1)
        self.text_edit = QtWidgets.QPlainTextEdit(self)
        self.text_edit.setObjectName("text_edit")
        self.gridLayout_3.addWidget(self.text_edit, 1, 0, 1, 2)
        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok|QtWidgets.QDialogButtonBox.Open|QtWidgets.QDialogButtonBox.Save)
        self.button_box.setObjectName("button_box")
        self.gridLayout_3.addWidget(self.button_box, 2, 0, 1, 2)

        self.retranslate_ui(self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslate_ui(self, text_io):
        _translate = _
        text_io.setWindowTitle(_translate("Dialog"))
        self.value_group_box.setTitle(_translate("Values"))
        self.id_label.setText(_translate("Identifier"))
        self.bib_radio_button.setText(_translate("Bib"))
        self.name_radio_button.setText(_translate("Person name"))
        self.value_label.setText(_translate("Value"))
        self.separator_group_box.setTitle(_translate("Separator"))
        self.space_radio_button.setText(_translate("space"))
        self.tab_radio_button.setText(_translate("tab"))
        self.semicolon_radio_button.setText(_translate("semicolon"))
        self.custom_radio_button.setText(_translate("custom"))
        self.text_edit.setPlainText('')

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
            logging.exception(e)

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
                        index += separator + arr[1]

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
            logging.exception(e)

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
        if person.result:
            return time_to_hhmmss(person.result.get_start_time())
        else:
            return time_to_hhmmss(person.start_time)
    elif key == _('Finish'):
        if person.result:
            return time_to_hhmmss(person.result.get_finish_time())
    elif key == _('Result'):
        if person.result:
            return person.result.get_result()
    elif key == _('Penalty time'):
        if person.result:
            return time_to_hhmmss(person.result.penalty_time)
    elif key == _('Penalty laps'):
        if person.result:
            return str(person.result.penalty_laps)
    elif key == _('Card number'):
        return str(person.card_number)
    elif key == _('Group'):
        if person.group:
            return person.group.name
    elif key == _('Team'):
        if person.organization:
            return person.organization.name
    elif key == _('Qualification'):
        return person.qual.get_title()

    return ''


def set_property(person, key, value):
    assert isinstance(person, Person)
    if key == _('Start'):
        if person.result:
            person.result.start_time = hhmmss_to_time(value)
        else:
            person.start_time = hhmmss_to_time(value)
    elif key == _('Finish'):
        if person.result:
            person.result.finish_time = hhmmss_to_time(value)
    elif key == _('Result'):
        None
    elif key == _('Penalty time'):
        if person.result:
            person.result.penalty_time = hhmmss_to_time(value)
    elif key == _('Penalty laps'):
        if person.result:
            person.result.penalty_laps = int(value)
    elif key == _('Card number'):
        person.card_number = int(value)
    elif key == _('Group'):
        None
    elif key == _('Team'):
        None
    elif key == _('Qualification'):
        None


def main(argv):
    app = QApplication(argv)
    TextExchangeDialog().exec()
    sys.exit(app.exec())

if __name__ == '__main__':
    main(sys.argv)
