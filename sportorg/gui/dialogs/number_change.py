from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QDialog

from sportorg import config
from sportorg.language import translate


class NumberChangeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.resize(319, 167)
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.setGeometry(QtCore.QRect(70, 120, 161, 32))
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(
            QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok
        )
        self.layoutWidget = QtWidgets.QWidget(self)
        self.layoutWidget.setGeometry(QtCore.QRect(14, 10, 290, 48))
        self.number_grid_layout = QtWidgets.QGridLayout(self.layoutWidget)
        self.number_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.source_num_label = QtWidgets.QLabel(self.layoutWidget)
        self.number_grid_layout.addWidget(self.source_num_label, 0, 0, 1, 1)
        self.source_num_spin_box = QtWidgets.QSpinBox(self.layoutWidget)
        self.source_num_spin_box.setMaximum(100000)
        self.number_grid_layout.addWidget(self.source_num_spin_box, 0, 1, 1, 1)
        self.source_info_label = QtWidgets.QLabel(self.layoutWidget)
        self.number_grid_layout.addWidget(self.source_info_label, 0, 2, 1, 1)
        self.target_num_label = QtWidgets.QLabel(self.layoutWidget)
        self.number_grid_layout.addWidget(self.target_num_label, 1, 0, 1, 1)
        self.target_num_spin_box = QtWidgets.QSpinBox(self.layoutWidget)
        self.target_num_spin_box.setMaximum(100000)
        self.number_grid_layout.addWidget(self.target_num_spin_box, 1, 1, 1, 1)
        self.target_info_label = QtWidgets.QLabel(self.layoutWidget)
        self.number_grid_layout.addWidget(self.target_info_label, 1, 2, 1, 1)
        self.layoutWidget1 = QtWidgets.QWidget(self)
        self.layoutWidget1.setGeometry(QtCore.QRect(14, 70, 256, 42))
        self.options_vert_layout = QtWidgets.QVBoxLayout(self.layoutWidget1)
        self.options_vert_layout.setContentsMargins(0, 0, 0, 0)
        self.remove_radio_button = QtWidgets.QRadioButton(self.layoutWidget1)
        self.remove_radio_button.setChecked(True)
        self.options_vert_layout.addWidget(self.remove_radio_button)
        self.replace_radio_button = QtWidgets.QRadioButton(self.layoutWidget1)
        self.options_vert_layout.addWidget(self.replace_radio_button)

        self.retranslateUi()
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        self.setWindowTitle(translate('Dialog'))
        self.setWindowIcon(QIcon(config.ICON))
        self.source_num_label.setText(translate('Source number'))
        self.source_info_label.setText(translate('Ivan Churakoff M21 11:09:00'))
        self.target_num_label.setText(translate('Target number'))
        self.target_info_label.setText(translate('Reserve M60 11:40:00'))
        self.remove_radio_button.setText(translate('Remove source'))
        self.replace_radio_button.setText(translate('Replace source with reserve'))
