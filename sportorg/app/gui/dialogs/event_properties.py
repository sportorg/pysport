import sys
import logging
from datetime import datetime

from PyQt5.QtCore import QTime
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QLineEdit, QApplication, QDialog, \
    QPushButton, QTextEdit, QDateEdit

from sportorg.app.gui.global_access import GlobalAccess
from sportorg.app.models.memory import race
from sportorg.app.modules.utils.custom_controls import AdvComboBox

from sportorg.language import _
from sportorg import config


def get_sport_kinds():
    ret = [_('orienteering'), _('running'), _('cross country')]
    return ret


def get_types():
    ret = [_('individual'), _('free order'), _('pursuit'), _('mass start'), _('one-man-relay'), _('relay')]
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
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

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
            except Exception as e:
                logging.exception(e)
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
        self.item_start_date.setDateTime(obj.get_setting('start_date', datetime.now()))
        self.item_end_date.setDateTime(obj.get_setting('end_date', datetime.now()))
        self.item_sport.setCurrentIndex(obj.get_setting('sport_kind_index', 0))
        self.item_type.setCurrentIndex(obj.get_setting('course_type_index', 0))

    def apply_changes_impl(self):
        changed = False
        obj = race()

        obj.set_setting('main_title', self.item_main_title.text())
        obj.set_setting('sub_title', self.item_sub_title.toPlainText())
        obj.set_setting('location', self.item_location.text())
        obj.set_setting('chief_referee', self.item_refery.text())
        obj.set_setting('secretary', self.item_secretary.text())
        obj.set_setting('start_date', self.item_start_date.dateTime())
        obj.set_setting('end_date', self.item_end_date.dateTime())
        obj.set_setting('sport_kind_index', self.item_sport.currentIndex())
        obj.set_setting('course_type_index', self.item_type.currentIndex())

        if changed:
            win = GlobalAccess().get_main_window()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EventPropertiesDialog()
    sys.exit(app.exec_())
