import logging

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSortFilterProxyModel
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QListView, QTableView

from sportorg.app.controller.dialogs.entry_edit import EntryEditDialog
from sportorg.app.models.table_model import PersonTableModel
from sportorg.language import _, get_languages


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setAcceptDrops(False)
        self.setToolTip("")
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)
        self.entry_layout = QtWidgets.QGridLayout(self)
        self.entry_layout.setObjectName("entry_layout")
        self.EntrySplitter = QtWidgets.QSplitter(self)
        self.EntrySplitter.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.EntrySplitter.setAutoFillBackground(True)
        self.EntrySplitter.setOrientation(QtCore.Qt.Horizontal)
        self.EntrySplitter.setObjectName("EntrySplitter")
        self.layout_widget = QtWidgets.QWidget(self.EntrySplitter)
        self.layout_widget.setObjectName("layout_widget")
        self.EntryDetails = QtWidgets.QFormLayout(self.layout_widget)
        self.EntryDetails.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.EntryDetails.setLabelAlignment(QtCore.Qt.AlignCenter)
        self.EntryDetails.setFormAlignment(QtCore.Qt.AlignCenter)
        self.EntryDetails.setContentsMargins(0, 0, 0, 0)
        self.EntryDetails.setHorizontalSpacing(1)
        self.EntryDetails.setObjectName("EntryDetails")
        self.EntryNameLabel = QtWidgets.QLabel(self.layout_widget)
        self.EntryNameLabel.setObjectName("EntryNameLabel")
        self.EntryDetails.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.EntryNameLabel)
        self.EntryNameEdit = QtWidgets.QLineEdit(self.layout_widget)
        self.EntryNameEdit.setObjectName("EntryNameEdit")
        self.EntryDetails.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.EntryNameEdit)
        self.EntryGroupLabel = QtWidgets.QLabel(self.layout_widget)
        self.EntryGroupLabel.setObjectName("EntryGroupLabel")
        self.EntryDetails.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.EntryGroupLabel)
        self.EntryGroupCombo = QtWidgets.QComboBox(self.layout_widget)
        self.EntryGroupCombo.setObjectName("EntryGroupCombo")
        self.EntryDetails.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.EntryGroupCombo)
        self.EntryTeamLabel = QtWidgets.QLabel(self.layout_widget)
        self.EntryTeamLabel.setObjectName("EntryTeamLabel")
        self.EntryDetails.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.EntryTeamLabel)
        self.EntryTeamCombo = QtWidgets.QComboBox(self.layout_widget)
        self.EntryTeamCombo.setObjectName("EntryTeamCombo")
        self.EntryDetails.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.EntryTeamCombo)
        self.EntryYearLabel = QtWidgets.QLabel(self.layout_widget)
        self.EntryYearLabel.setObjectName("EntryYearLabel")
        self.EntryDetails.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.EntryYearLabel)
        self.EntryYearSpinBox = QtWidgets.QSpinBox(self.layout_widget)
        self.EntryYearSpinBox.setReadOnly(False)
        self.EntryYearSpinBox.setMinimum(1900)
        self.EntryYearSpinBox.setMaximum(2070)
        self.EntryYearSpinBox.setProperty("value", 1900)
        self.EntryYearSpinBox.setObjectName("EntryYearSpinBox")
        self.EntryDetails.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.EntryYearSpinBox)
        self.EntryBirthDayLabel = QtWidgets.QLabel(self.layout_widget)
        self.EntryBirthDayLabel.setObjectName("EntryBirthDayLabel")
        self.EntryDetails.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.EntryBirthDayLabel)
        self.EntryBirthDayEdit = QtWidgets.QDateEdit(self.layout_widget)
        self.EntryBirthDayEdit.setObjectName("EntryBirthDayEdit")
        self.EntryDetails.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.EntryBirthDayEdit)
        self.EntryQualLabel = QtWidgets.QLabel(self.layout_widget)
        self.EntryQualLabel.setObjectName("EntryQualLabel")
        self.EntryDetails.setWidget(6, QtWidgets.QFormLayout.LabelRole, self.EntryQualLabel)
        self.EntryQualCombo = QtWidgets.QComboBox(self.layout_widget)
        self.EntryQualCombo.setObjectName("EntryQualCombo")
        self.EntryDetails.setWidget(6, QtWidgets.QFormLayout.FieldRole, self.EntryQualCombo)
        self.EntryLine = QtWidgets.QFrame(self.layout_widget)
        self.EntryLine.setFrameShape(QtWidgets.QFrame.HLine)
        self.EntryLine.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.EntryLine.setObjectName("EntryLine")
        self.EntryDetails.setWidget(7, QtWidgets.QFormLayout.SpanningRole, self.EntryLine)
        self.EntryStartLabel = QtWidgets.QLabel(self.layout_widget)
        self.EntryStartLabel.setObjectName("EntryStartLabel")
        self.EntryDetails.setWidget(8, QtWidgets.QFormLayout.LabelRole, self.EntryStartLabel)
        self.EntryStartEdit = QtWidgets.QTimeEdit(self.layout_widget)
        self.EntryStartEdit.setObjectName("EntryStartEdit")
        self.EntryDetails.setWidget(8, QtWidgets.QFormLayout.FieldRole, self.EntryStartEdit)
        self.EntryBibNumber = QtWidgets.QLabel(self.layout_widget)
        self.EntryBibNumber.setObjectName("EntryBibNumber")
        self.EntryDetails.setWidget(9, QtWidgets.QFormLayout.LabelRole, self.EntryBibNumber)
        self.EntryBibSpinBox = QtWidgets.QSpinBox(self.layout_widget)
        self.EntryBibSpinBox.setMinimum(1900)
        self.EntryBibSpinBox.setMaximum(2070)
        self.EntryBibSpinBox.setProperty("value", 1900)
        self.EntryBibSpinBox.setObjectName("EntryBibSpinBox")
        self.EntryDetails.setWidget(9, QtWidgets.QFormLayout.FieldRole, self.EntryBibSpinBox)

        self.EntryTable = QtWidgets.QTableView(self.EntrySplitter)
        self.EntryTable.setObjectName("EntryTable")
        proxy_model = QSortFilterProxyModel(self)
        proxy_model.setSourceModel(PersonTableModel())
        self.EntryTable.setModel(proxy_model)
        self.EntryTable.setSortingEnabled(True)
        self.EntryTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        hor_reader = self.EntryTable.horizontalHeader()
        assert (isinstance(hor_reader, QHeaderView))
        hor_reader.setSectionsMovable(True)
        hor_reader.setDropIndicatorShown(True)
        hor_reader.setSectionResizeMode(QHeaderView.ResizeToContents)

        def show_edit_dialog(self, index):
            EntryEditDialog()

        def entry_double_clicked(index):
            print('clicked on ' + str(index.row()))
            logging.info('clicked on ' + str(index.row()))
            # show_edit_dialog(index)
            try:
                dialog = EntryEditDialog(self.EntryTable, index)
            except:
                print (sys.exc_info())

            dialog.exec()




        self.EntryTable.doubleClicked.connect(entry_double_clicked)
        self.entry_layout.addWidget(self.EntrySplitter)

    def get_table(self):
        return self.EntryTable

