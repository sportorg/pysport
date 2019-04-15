import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QFormLayout, QLabel, QLineEdit, QDialog, QDialogButtonBox

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.constant import get_countries, get_regions
from sportorg.models.memory import race, Organization, find
from sportorg.modules.teamwork import Teamwork


class OrganizationEditDialog(QDialog):
    def __init__(self, organization, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        assert (isinstance(organization, Organization))
        self.current_object = organization
        self.is_new = is_new

    def exec_(self):
        self.init_ui()
        self.set_values_from_model()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_('Team properties'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_name = QLabel(_('Name'))
        self.item_name = QLineEdit()
        self.item_name.textChanged.connect(self.check_name)
        self.layout.addRow(self.label_name, self.item_name)

        self.label_code = QLabel(_('Code'))
        self.item_code = QLineEdit()
        self.layout.addRow(self.label_code, self.item_code)

        self.label_country = QLabel(_('Country'))
        self.item_country = AdvComboBox()
        self.item_country.addItems(get_countries())
        self.layout.addRow(self.label_country, self.item_country)

        self.label_region = QLabel(_('Region'))
        self.item_region = AdvComboBox()
        self.item_region.addItems(get_regions())
        self.layout.addRow(self.label_region, self.item_region)

        self.label_contact = QLabel(_('Contact'))
        self.item_contact = QLineEdit()
        self.layout.addRow(self.label_contact, self.item_contact)

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

        self.show()

    def check_name(self):
        name = self.item_name.text()
        self.button_ok.setDisabled(False)
        if name and name != self.current_object.name:
            org = find(race().organizations, name=name)
            if org:
                self.button_ok.setDisabled(True)

    def set_values_from_model(self):

        self.item_name.setText(self.current_object.name)
        self.item_name.selectAll()

        self.item_code.setText(self.current_object.code)
        self.item_country.setCurrentText(self.current_object.country)
        self.item_region.setCurrentText(self.current_object.region)
        self.item_contact.setText(self.current_object.contact)

    def apply_changes_impl(self):
        org = self.current_object
        assert (isinstance(org, Organization))
        if self.is_new:
            race().organizations.insert(0, org)

        org.name = self.item_name.text()
        org.code = self.item_code.text()
        org.country = self.item_country.currentText()
        org.region = self.item_region.currentText()
        org.contact = self.item_contact.text()

        org.generate_cache()
        Teamwork().send(org.to_dict())
