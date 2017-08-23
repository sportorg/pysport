# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog_number_change.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication


class NumberChangeDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.setObjectName("number_change")
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.resize(319, 167)
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.setGeometry(QtCore.QRect(70, 120, 161, 32))
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.button_box.setObjectName("button_box")
        self.layoutWidget = QtWidgets.QWidget(self)
        self.layoutWidget.setGeometry(QtCore.QRect(14, 10, 290, 48))
        self.layoutWidget.setObjectName("layoutWidget")
        self.number_grid_layout = QtWidgets.QGridLayout(self.layoutWidget)
        self.number_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.number_grid_layout.setObjectName("number_grid_layout")
        self.source_num_label = QtWidgets.QLabel(self.layoutWidget)
        self.source_num_label.setObjectName("source_num_label")
        self.number_grid_layout.addWidget(self.source_num_label, 0, 0, 1, 1)
        self.source_num_spin_box = QtWidgets.QSpinBox(self.layoutWidget)
        self.source_num_spin_box.setMaximum(100000)
        self.source_num_spin_box.setObjectName("source_num_spin_box")
        self.number_grid_layout.addWidget(self.source_num_spin_box, 0, 1, 1, 1)
        self.source_info_label = QtWidgets.QLabel(self.layoutWidget)
        self.source_info_label.setObjectName("source_info_label")
        self.number_grid_layout.addWidget(self.source_info_label, 0, 2, 1, 1)
        self.target_num_label = QtWidgets.QLabel(self.layoutWidget)
        self.target_num_label.setObjectName("target_num_label")
        self.number_grid_layout.addWidget(self.target_num_label, 1, 0, 1, 1)
        self.target_num_spin_box = QtWidgets.QSpinBox(self.layoutWidget)
        self.target_num_spin_box.setMaximum(100000)
        self.target_num_spin_box.setObjectName("target_num_spin_box")
        self.number_grid_layout.addWidget(self.target_num_spin_box, 1, 1, 1, 1)
        self.target_info_label = QtWidgets.QLabel(self.layoutWidget)
        self.target_info_label.setObjectName("target_info_label")
        self.number_grid_layout.addWidget(self.target_info_label, 1, 2, 1, 1)
        self.layoutWidget1 = QtWidgets.QWidget(self)
        self.layoutWidget1.setGeometry(QtCore.QRect(14, 70, 161, 42))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.options_vert_layout = QtWidgets.QVBoxLayout(self.layoutWidget1)
        self.options_vert_layout.setContentsMargins(0, 0, 0, 0)
        self.options_vert_layout.setObjectName("options_vert_layout")
        self.remove_radio_button = QtWidgets.QRadioButton(self.layoutWidget1)
        self.remove_radio_button.setChecked(True)
        self.remove_radio_button.setObjectName("remove_radio_button")
        self.options_vert_layout.addWidget(self.remove_radio_button)
        self.replace_radio_button = QtWidgets.QRadioButton(self.layoutWidget1)
        self.replace_radio_button.setObjectName("replace_radio_button")
        self.options_vert_layout.addWidget(self.replace_radio_button)

        self.retranslateUi()
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("number_change", "Dialog"))
        self.source_num_label.setText(_translate("number_change", "Source number"))
        self.source_info_label.setText(_translate("number_change", "Ivan Churakoff M21 11:09:00"))
        self.target_num_label.setText(_translate("number_change", "Target number"))
        self.target_info_label.setText(_translate("number_change", "Reserve M60 11:40:00"))
        self.remove_radio_button.setText(_translate("number_change", "Remove source"))
        self.replace_radio_button.setText(_translate("number_change", "Replace source with reserve"))


def main(argv):

    NumberChangeDialog().show()

    app = QApplication(argv)
    sys.exit(app.exec())


if __name__ == '__main__':
    main(sys.argv)
