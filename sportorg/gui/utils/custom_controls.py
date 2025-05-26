try:
    from PySide6 import QtCore
    from PySide6.QtCore import QSortFilterProxyModel, QTime
    from PySide6.QtWidgets import (
        QComboBox,
        QCompleter,
        QMessageBox,
        QSpinBox,
        QTimeEdit,
    )
except ModuleNotFoundError:
    from PySide2 import QtCore
    from PySide2.QtCore import QSortFilterProxyModel, QTime
    from PySide2.QtWidgets import (
        QComboBox,
        QCompleter,
        QMessageBox,
        QSpinBox,
        QTimeEdit,
    )

from sportorg.common.otime import OTime
from sportorg.language import translate
from sportorg.utils.time import time_to_otime, time_to_qtime


class AdvComboBox(QComboBox):
    """
    Combo with autocomplete
    Found in Internet by Sergei
    """

    def __init__(self, parent=None, val_list=None, max_width=0):
        super(AdvComboBox, self).__init__(parent)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)

        # add a filter model to filter matching items
        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        # add a completer, which uses the filter model
        self.completer = QCompleter(self.pFilterModel, self)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)

        self.setCompleter(self.completer)

        # connect signals

        def filter_function(text):
            self.pFilterModel.setFilterFixedString(str(text))

        self.lineEdit().textEdited.connect(filter_function)
        self.completer.activated.connect(self.on_completer_activated)

        if val_list:
            self.addItems(val_list)

        if max_width > 0:
            self.setMaximumWidth(max_width)

    def wheelEvent(self, ev):
        if ev.type() == QtCore.QEvent.Wheel:
            ev.ignore()

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        if text:
            index = self.findText(str(text))
            self.setCurrentIndex(index)


class AdvSpinBox(QSpinBox):
    def __init__(self, minimum=0, maximum=99999999, value=0, max_width=0, parent=None):
        super(AdvSpinBox, self).__init__(parent)
        self.setMinimum(minimum)
        self.setMaximum(maximum)
        self.setValue(max(value, minimum))
        if max_width > 0:
            self.setMaximumWidth(max_width)

    def wheelEvent(self, ev):
        if ev.type() == QtCore.QEvent.Wheel:
            ev.ignore()


class AdvTimeEdit(QTimeEdit):
    def __init__(self, time=OTime(), max_width=0, display_format=None, parent=None):
        super(AdvTimeEdit, self).__init__(parent)

        if isinstance(time, OTime):
            self.setOTime(time)
        elif isinstance(time, QTime):
            self.setTime(time)

        if max_width > 10:
            self.setMaximumWidth(max_width)

        if display_format:
            self.setDisplayFormat(display_format)

    def setOTime(self, new_time):
        self.setTime(time_to_qtime(new_time))

    def getOTime(self):
        return time_to_otime(self.time())

    def wheelEvent(self, ev):
        if ev.type() == QtCore.QEvent.Wheel:
            ev.ignore()


def messageBoxQuestion(
    parent=None, title="", text="", buttons=(QMessageBox.Yes | QMessageBox.No)
):
    messageBox = QMessageBox(QMessageBox.Question, title, text, buttons, parent)

    button_yes = messageBox.button(QMessageBox.Yes)
    if button_yes:
        button_yes.setText(translate("Yes"))

    button_no = messageBox.button(QMessageBox.No)
    if button_no:
        button_no.setText(translate("No"))

    button_save = messageBox.button(QMessageBox.Save)
    if button_save:
        button_save.setText(translate("Save"))

    button_cancel = messageBox.button(QMessageBox.Cancel)
    if button_cancel:
        button_cancel.setText(translate("Cancel"))

    return messageBox.exec_()
