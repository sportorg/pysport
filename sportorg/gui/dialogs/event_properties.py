import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QLineEdit, QDialog, QTextEdit, QDateTimeEdit, \
    QDialogButtonBox, QSpinBox

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.memory import race, RaceType
from sportorg.models.result.result_calculation import ResultCalculation


class EventPropertiesDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec(self):
        self.init_ui()
        return super().exec()

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
        self.item_start_date = QDateTimeEdit()
        self.item_start_date.setDisplayFormat('yyyy.MM.dd HH:mm:ss')
        self.layout.addRow(self.label_start_date, self.item_start_date)

        self.label_end_date = QLabel(_('End date'))
        # self.item_end_date = QCalendarWidget()
        self.item_end_date = QDateTimeEdit()
        self.item_end_date.setDisplayFormat('yyyy.MM.dd HH:mm:ss')
        self.layout.addRow(self.label_end_date, self.item_end_date)

        self.label_location = QLabel(_('Location'))
        self.item_location = QLineEdit()
        self.layout.addRow(self.label_location, self.item_location)

        self.label_type = QLabel(_('Event type'))
        self.item_type = AdvComboBox()
        self.item_type.addItems(RaceType.get_titles())
        self.layout.addRow(self.label_type, self.item_type)

        self.label_relay_legs = QLabel(_('Relay legs'))
        self.item_relay_legs = QSpinBox()
        self.item_relay_legs.setMinimum(1)
        self.item_relay_legs.setMaximum(20)
        self.item_relay_legs.setValue(3)
        self.layout.addRow(self.label_relay_legs, self.item_relay_legs)

        self.item_type.currentTextChanged.connect(self.change_type)

        self.label_refery = QLabel(_('Chief referee'))
        self.item_refery = QLineEdit()
        self.layout.addRow(self.label_refery, self.item_refery)

        self.label_secretary = QLabel(_('Secretary'))
        self.item_secretary = QLineEdit()
        self.layout.addRow(self.label_secretary, self.item_secretary)

        self.label_url = QLabel(_('URL'))
        self.item_url = QLineEdit()
        self.layout.addRow(self.label_url, self.item_url)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.error(str(e))
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.set_values_from_model()

        self.show()

    def change_type(self):
        flag = self.item_type.currentText() == RaceType.RELAY.get_title()
        self.label_relay_legs.setVisible(flag)
        self.item_relay_legs.setVisible(flag)

    def set_values_from_model(self):
        obj = race()
        self.item_main_title.setText(str(obj.data.title))
        self.item_sub_title.setText(str(obj.data.description))
        self.item_location.setText(str(obj.data.location))
        self.item_url.setText(str(obj.data.url))
        self.item_refery.setText(str(obj.data.chief_referee))
        self.item_secretary.setText(str(obj.data.secretary))
        self.item_start_date.setDateTime(obj.data.get_start_datetime())
        self.item_end_date.setDateTime(obj.data.get_end_datetime())
        self.item_type.setCurrentIndex(obj.data.race_type.value)
        self.item_relay_legs.setValue(obj.data.relay_leg_count)
        self.change_type()

    def apply_changes_impl(self):
        changed = True
        obj = race()

        start_date = self.item_start_date.dateTime().toPyDateTime()
        end_date = self.item_end_date.dateTime().toPyDateTime()

        obj.data.title = self.item_main_title.text()
        obj.data.description = self.item_sub_title.toPlainText()
        obj.data.location = self.item_location.text()
        obj.data.url = self.item_url.text()
        obj.data.chief_referee = self.item_refery.text()
        obj.data.secretary = self.item_secretary.text()
        obj.data.start_datetime = start_date
        obj.data.end_datetime = end_date
        obj.data.race_type = RaceType(self.item_type.currentIndex())
        obj.data.relay_leg_count = self.item_relay_legs.value()

        obj.set_setting('sportident_zero_time', (
            start_date.hour,
            start_date.minute,
            0
        ))

        if changed:
            ResultCalculation(race()).process_results()
            GlobalAccess().get_main_window().refresh()
