import logging

from PyQt5.QtCore import QModelIndex
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QLineEdit, QDialog, QPushButton, QDialogButtonBox

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.constant import get_countries, get_regions
from sportorg.models.memory import race, Organization


class OrganizationEditDialog(QDialog):
    def __init__(self, table=None, index=None):
        super().__init__(GlobalAccess().get_main_window())
        if table is not None:
            self.table = table
            self.current_index = index

            assert (isinstance(index, QModelIndex))
            current_object = race().organizations[index.row()]
            assert (isinstance(current_object, Organization))
            self.current_object = current_object

    def exec(self):
        self.init_ui()
        self.set_values_from_table()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Team properties'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_name = QLabel(_('Name'))
        self.item_name = QLineEdit()
        self.layout.addRow(self.label_name, self.item_name)

        self.label_country = QLabel(_('Country'))
        self.item_country = AdvComboBox()
        self.item_country.addItems(get_countries())
        self.layout.addRow(self.label_country, self.item_country)

        self.label_region = QLabel(_('Region'))
        self.item_region = AdvComboBox()
        self.item_region.addItems(get_regions())
        self.layout.addRow(self.label_region, self.item_region)

        self.label_city = QLabel(_('City'))
        self.item_city = QLineEdit()
        self.layout.addRow(self.label_city, self.item_city)

        self.label_address = QLabel(_('Address'))
        self.item_address = QLineEdit()
        self.layout.addRow(self.label_address, self.item_address)

        self.label_contact = QLabel(_('Contact'))
        self.item_contact = QLineEdit()
        self.layout.addRow(self.label_contact, self.item_contact)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(str(e))
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def set_values_from_table(self):

        self.item_name.setText(self.current_object.name)
        self.item_city.setText(self.current_object.address.city)

        if self.current_object.address.country is not None:
            self.item_country.setCurrentText(self.current_object.address.country.name)
        if self.current_object.address.state:
            self.item_region.setCurrentText(self.current_object.address.state)
        if self.current_object.contact is not None:
            self.item_contact.setText(self.current_object.contact.value)
        if self.current_object.address is not None:
            self.item_address.setText(self.current_object.address.street)

    def apply_changes_impl(self):
        changed = False
        org = self.current_object
        assert (isinstance(org, Organization))

        if org.name != self.item_name.text():
            org.name = self.item_name.text()
            changed = True

        if org.address.country.name != self.item_country.currentText():
            org.address.country.name = self.item_country.currentText()
            changed = True

        if org.address.state != self.item_region.currentText():
            org.address.state = self.item_region.currentText()
            changed = True

        if org.address.city != self.item_city.text():
            org.address.city = self.item_city.text()
            changed = True

        if org.address.street != self.item_address.text():
            org.address.street = self.item_address.text()
            changed = True

        if org.contact.value != self.item_contact.text():
            org.contact.value = self.item_contact.text()
            org.contact.name = 'phone'
            changed = True

        if changed:
            GlobalAccess().get_main_window().refresh()
            # table.model().sourceModel().update_one_object(part, table.model().mapToSource(self.current_index).row())
