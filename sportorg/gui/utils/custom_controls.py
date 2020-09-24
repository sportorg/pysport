from PySide2 import QtCore
from PySide2.QtCore import QSortFilterProxyModel
from PySide2.QtWidgets import QComboBox, QCompleter, QMessageBox

from sportorg.language import translate


class AdvComboBox(QComboBox):
    """
    Combo with autocomplete
    Found in Internet by Sergei
    """

    def __init__(self, parent=None):
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

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        if text:
            index = self.findText(str(text))
            self.setCurrentIndex(index)


def messageBoxQuestion(
    parent=None, title='', text='', buttons=(QMessageBox.Yes | QMessageBox.No)
):
    messageBox = QMessageBox(QMessageBox.Question, title, text, buttons, parent)

    button_yes = messageBox.button(QMessageBox.Yes)
    if button_yes:
        button_yes.setText(translate('Yes'))

    button_no = messageBox.button(QMessageBox.No)
    if button_no:
        button_no.setText(translate('No'))

    button_save = messageBox.button(QMessageBox.Save)
    if button_save:
        button_save.setText(translate('Save'))

    button_cancel = messageBox.button(QMessageBox.Cancel)
    if button_cancel:
        button_cancel.setText(translate('Cancel'))

    return messageBox.exec_()
