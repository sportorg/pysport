# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog_text_io.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog


class Ui_text_io(object):
    def setupUi(self, text_io):
        text_io.setObjectName("text_io")
        text_io.setWindowModality(QtCore.Qt.WindowModal)
        text_io.resize(319, 462)
        text_io.setSizeGripEnabled(False)
        text_io.setModal(True)
        self.gridLayout_3 = QtWidgets.QGridLayout(text_io)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.value_group_box = QtWidgets.QGroupBox(text_io)
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
        self.gridLayout_2.addWidget(self.value_combo_box, 1, 1, 1, 1)
        self.id_label.raise_()
        self.bib_radio_button.raise_()
        self.value_label.raise_()
        self.value_combo_box.raise_()
        self.gridLayout_3.addWidget(self.value_group_box, 0, 0, 1, 1)
        self.separator_group_box = QtWidgets.QGroupBox(text_io)
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
        self.text_edit = QtWidgets.QPlainTextEdit(text_io)
        self.text_edit.setObjectName("text_edit")
        self.gridLayout_3.addWidget(self.text_edit, 1, 0, 1, 2)
        self.button_box = QtWidgets.QDialogButtonBox(text_io)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok|QtWidgets.QDialogButtonBox.Open|QtWidgets.QDialogButtonBox.Save)
        self.button_box.setObjectName("button_box")
        self.gridLayout_3.addWidget(self.button_box, 2, 0, 1, 2)

        self.retranslateUi(text_io)
        self.button_box.accepted.connect(text_io.accept)
        self.button_box.rejected.connect(text_io.reject)
        QtCore.QMetaObject.connectSlotsByName(text_io)

    def retranslateUi(self, text_io):
        _translate = QtCore.QCoreApplication.translate
        text_io.setWindowTitle(_translate("text_io", "Dialog"))
        self.value_group_box.setTitle(_translate("text_io", "Values"))
        self.id_label.setText(_translate("text_io", "Identifier"))
        self.bib_radio_button.setText(_translate("text_io", "Bib number"))
        self.name_radio_button.setText(_translate("text_io", "Name"))
        self.value_label.setText(_translate("text_io", "Value"))
        self.separator_group_box.setTitle(_translate("text_io", "Separator"))
        self.space_radio_button.setText(_translate("text_io", "space"))
        self.tab_radio_button.setText(_translate("text_io", "tab"))
        self.semicolon_radio_button.setText(_translate("text_io", "semicolon"))
        self.custom_radio_button.setText(_translate("text_io", "custom"))
        self.text_edit.setPlainText(_translate("text_io", "101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"101 11:02:00\n"
"Akhtarov Danil 12:10:00\n"
"Akhtarov Danil 12:10:00\n"
""))


def main(argv):
    app = QApplication(argv)
    mw = QDialog()
    obj = Ui_text_io()
    obj.setupUi(mw)
    mw.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main(sys.argv)
