import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QRadioButton,
)

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import translate
from sportorg.models.memory import find, race


class SportOrgImportDialog(QDialog):
    def __init__(self, races, current_race=0):
        super().__init__(GlobalAccess().get_main_window())
        self.races = races
        self.current_race = current_race

    def exec_(self):
        self.init_ui()
        self.set_values()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate('Import'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.item_races = AdvComboBox()
        self.layout.addRow(QLabel(translate('Choose race')), self.item_races)

        self.unique_id_box = QGroupBox(translate('Unique id'))
        self.unique_id_box_layout = QFormLayout()
        self.unique_id_item_id = QRadioButton(translate('Id'))
        self.unique_id_item_id.setChecked(True)
        self.unique_id_box_layout.addRow(self.unique_id_item_id)
        self.unique_id_item_name = QRadioButton(translate('Name'))
        self.unique_id_item_name.setDisabled(True)
        self.unique_id_box_layout.addRow(self.unique_id_item_name)
        self.unique_id_box.setLayout(self.unique_id_box_layout)
        self.layout.addRow(self.unique_id_box)

        self.import_action_box = QGroupBox(translate('Action'))
        self.import_action_box_layout = QFormLayout()
        self.import_action_item_add = QRadioButton(translate('Add'))
        self.import_action_box_layout.addRow(self.import_action_item_add)
        self.import_action_item_overwrite = QRadioButton(translate('Overwrite'))
        self.import_action_item_overwrite.setChecked(True)
        self.import_action_box_layout.addRow(self.import_action_item_overwrite)
        self.import_action_box.setLayout(self.import_action_box_layout)
        self.layout.addRow(self.import_action_box)

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
        self.button_ok.setText(translate('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def set_values(self):
        self.fill_race_list()

    def apply_changes_impl(self):
        import_race = self.races[self.item_races.currentIndex()]
        unique_id = 'id'
        if self.unique_id_item_name.isChecked():
            unique_id = 'name'
        action = 'add'
        if self.import_action_item_overwrite.isChecked():
            action = 'overwrite'

        obj = race()

        if unique_id == 'id' and action == 'overwrite':
            import_race.id = obj.id
            obj.update_data(import_race.to_dict())
            return

        if unique_id == 'id' and action == 'add':
            organizations = []
            for org in import_race.organizations:
                old_org = find(obj.organizations, id=org.id)
                old_org_by_name = find(obj.organizations, name=org.name)
                if old_org is None:
                    if old_org_by_name:
                        org.name = '_' + org.name
                    organizations.append(org)
            obj.organizations.extend(organizations)

            courses = []
            for course in import_race.courses:
                old_course = find(obj.courses, id=course.id)
                old_course_by_name = find(obj.courses, name=course.name)
                if old_course is None:
                    if old_course_by_name:
                        course.name = '_' + course.name
                    courses.append(course)
            obj.courses.extend(courses)

            groups = []
            for group in import_race.groups:
                old_group = find(obj.groups, id=group.id)
                old_group_by_name = find(obj.groups, name=group.name)
                if old_group is None:
                    if old_group_by_name:
                        group.name = '_' + group.name
                    if group.course:
                        group.course = find(obj.courses, id=group.course.id)
                    groups.append(group)
            obj.groups.extend(groups)

            persons = []
            for person in import_race.persons:
                if find(obj.persons, id=person.id) is None:
                    if person.group:
                        person.group = find(obj.groups, id=person.group.id)
                    if person.organization:
                        person.organization = find(
                            obj.organizations, id=person.organization.id
                        )
                    persons.append(person)
            obj.persons.extend(persons)

            results = []
            for result in import_race.results:
                if find(obj.results, id=result.id) is None:
                    if result.person:
                        result.person = find(obj.persons, id=result.person.id)
                    results.append(result)
            obj.results.extend(results)
            return

    def fill_race_list(self):
        race_list = []

        self.item_races.clear()
        for cur_race in self.races:
            race_list.append(str(cur_race.data.get_start_datetime()))
        self.item_races.addItems(race_list)

        self.item_races.setCurrentIndex(self.current_race)
