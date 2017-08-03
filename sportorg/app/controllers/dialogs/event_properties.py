import sys
import traceback

from PyQt5 import QtCore
from PyQt5.QtCore import QSortFilterProxyModel
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QLineEdit, QComboBox, QCompleter, QApplication, QDialog, \
    QPushButton, QTextEdit, QDateEdit

from sportorg.app.controllers.global_access import GlobalAccess
from sportorg.app.models.memory import race

from sportorg.language import _

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

def get_sport_kinds():
    ret = list()
    ret.append(_('orienteering'))
    ret.append(_('running'))
    ret.append(_('cross country'))
    return ret

def get_types():
    ret = list()
    ret.append(_('individual'))
    ret.append(_('free order'))
    ret.append(_('pursuit'))
    ret.append(_('mass start'))
    ret.append(_('one-man-relay'))
    ret.append(_('relay'))
    return ret

class EventPropertiesDialog(QDialog):
    def __init__(self, table=None, index=None):
        super().__init__()
        self.init_ui()

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setFixedWidth(500)
        self.setWindowTitle(_('Event properties'))
        self.setWindowIcon(QIcon('sportorg.ico'))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.setToolTip(_('Event Properties Window'))

        self.layout = QFormLayout(self)

        self.label_main_title = QLabel(_('Main title'))
        self.item_main_title = QLineEdit()
        self.layout.addRow(self.label_main_title, self.item_main_title)

        self.label_sub_title = QLabel(_('Sub title'))
        self.item_sub_title = QTextEdit()
        self.item_sub_title.setMaximumHeight(100)
        self.layout.addRow(self.label_sub_title, self.item_sub_title)

        self.label_start_date = QLabel(_('Start date'))
        self.item_start_date = QDateEdit()
        self.layout.addRow(self.label_start_date, self.item_start_date)

        self.label_end_date = QLabel(_('End date'))
        # self.item_end_date = QCalendarWidget()
        self.item_end_date = QDateEdit()
        self.layout.addRow(self.label_end_date, self.item_end_date)

        self.label_location = QLabel(_('Location'))
        self.item_location = QLineEdit()
        self.layout.addRow(self.label_location, self.item_location)

        self.label_sport = QLabel(_('Sport kind'))
        self.item_sport = AdvComboBox()
        self.item_sport.addItems(get_sport_kinds())
        self.layout.addRow(self.label_sport, self.item_sport)

        self.label_type = QLabel(_('Event type'))
        self.item_type = AdvComboBox()
        self.item_type.addItems(get_types())
        self.layout.addRow(self.label_type, self.item_type)

        self.label_refery = QLabel(_('Chief referee'))
        self.item_refery = QLineEdit()
        self.layout.addRow(self.label_refery, self.item_refery)

        self.label_secretary = QLabel(_('Secretary'))
        self.item_secretary = QLineEdit()
        self.layout.addRow(self.label_secretary, self.item_secretary)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except:
                print(sys.exc_info())
                traceback.print_exc()
            self.close()

        self.button_ok = QPushButton(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

        self.set_values_from_model()

        self.show()

    def set_values_from_model(self):
        obj = race()
        self.item_main_title.setText(str(obj.get_setting('main_title')))
        self.item_sub_title.setText(str(obj.get_setting('sub_title')))
        self.item_location.setText(str(obj.get_setting('location')))
        self.item_refery.setText(str(obj.get_setting('chief_referee')))
        self.item_secretary.setText(str(obj.get_setting('secretary')))


    def apply_changes_impl(self):
        changed = False
        obj = race()

        obj.set_setting('main_title', self.item_main_title.text())
        obj.set_setting('sub_title', self.item_sub_title.toPlainText())
        obj.set_setting('location', self.item_location.text())
        obj.set_setting('chief_referee', self.item_refery.text())
        obj.set_setting('secretary', self.item_secretary.text())

        if changed:
            win = self.get_main_window()

    def get_main_window(self):
        return GlobalAccess().get_main_window()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EventPropertiesDialog()
    sys.exit(app.exec_())
