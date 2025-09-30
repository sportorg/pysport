import logging

try:
    from PySide6 import QtCore, QtWidgets
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit
except ModuleNotFoundError:
    from PySide2 import QtCore, QtWidgets
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import translate
from sportorg.models.constant import get_countries, get_race_teams, get_regions
from sportorg.models.memory import find, race


class OrganizationMassEditDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        max_field_width = 200

        self.orzanization_checkbox = QtWidgets.QCheckBox(self)
        self.orzanization_combo = AdvComboBox(
            self, val_list=get_race_teams(), max_width=max_field_width
        )
        self.layout.addRow(self.orzanization_checkbox, self.orzanization_combo)

        self.code_checkbox = QtWidgets.QCheckBox(self)
        self.code_textedit = QLineEdit(self)
        self.code_textedit.setMaximumHeight(23)
        self.code_textedit.setMaximumWidth(max_field_width)
        self.layout.addRow(self.code_checkbox, self.code_textedit)

        self.country_checkbox = QtWidgets.QCheckBox(self)
        self.country_combo = AdvComboBox(
            self, val_list=get_countries(), max_width=max_field_width
        )
        self.layout.addRow(self.country_checkbox, self.country_combo)

        self.region_checkbox = QtWidgets.QCheckBox(self)
        self.region_combo = AdvComboBox(self, val_list=get_regions())
        self.region_combo.setMaximumWidth(max_field_width)
        self.layout.addRow(self.region_checkbox, self.region_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.clicked.connect(self.accept)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.clicked.connect(self.reject)

        self.layout.addRow(button_box)

        self.translate_ui()

        self.show()

    def accept(self, *args, **kwargs):
        try:
            # apply mass edit here
            mv = GlobalAccess().get_main_window()
            selection = mv.get_selected_rows(mv.get_table_by_name("OrganizationTable"))
            if selection:
                obj = race()

                change_organization = find(
                    obj.organizations, name=self.orzanization_combo.currentText()
                )
                change_code = self.code_textedit.text()
                change_country = self.country_combo.currentText()
                change_region = self.region_combo.currentText()

                for i in reversed(selection):
                    if i < len(obj.organizations):
                        cur_organization = obj.organizations[i]

                        if self.orzanization_checkbox.isChecked():
                            # find all people of selected organization and change organization to new value
                            if cur_organization != change_organization:
                                for person in obj.persons:
                                    if person.organization == cur_organization:
                                        person.organization = change_organization
                                obj.organizations.remove(cur_organization)

                        if self.code_checkbox.isChecked():
                            cur_organization.code = change_code

                        if self.country_checkbox.isChecked():
                            cur_organization.country = change_country

                        if self.region_checkbox.isChecked():
                            cur_organization.region = change_region

        except Exception as e:
            logging.exception(e)

        super().accept(*args, **kwargs)

    def translate_ui(self):
        self.setWindowTitle(translate("Mass Edit Dialog"))
        self.orzanization_checkbox.setText(translate("Team"))
        self.code_checkbox.setText(translate("Code"))
        self.country_checkbox.setText(translate("Country"))
        self.region_checkbox.setText(translate("Region"))

        self.button_ok.setText(translate("OK"))
        self.button_cancel.setText(translate("Cancel"))
