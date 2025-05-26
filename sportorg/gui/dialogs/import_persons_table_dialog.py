import logging
from enum import Enum

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QTableWidget,
        QTableWidgetItem,
        QApplication,
    )
except ModuleNotFoundError:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QTableWidget,
        QTableWidgetItem,
        QApplication,
    )

from sportorg import config
from sportorg.gui.dialogs.text_io import set_property
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import translate
from sportorg.models import memory
from sportorg.models.memory import find, race
from sportorg.utils.time import ddmmyyyy_to_time


class ImportPersonsTableDialog(QDialog):
    class ExtendedEnum(Enum):
        @classmethod
        def list(cls):
            return list(map(lambda c: c.value, cls))

        @classmethod
        def name(cls, val):
            return {v: k for k, v in dict(vars(cls)).items() if isinstance(v, int)}.get(
                val, None
            )

    class HEADER(ExtendedEnum):
        NONE = ""
        BIB = translate("Bib")
        GROUP = translate("Group")
        TEAM = translate("Team")
        NAME = translate("First name")
        SURNAME = translate("Last name")
        MIDDLE_NAME = translate("Middle name")
        YEAR = translate("Year of birth")
        BIRTHDAY = translate("Birthday")
        COMMENT = translate("Comment")
        QUAL = translate("Qualification")
        CARD = translate("Card number")
        START = translate("Start")
        FINISH = translate("Finish")
        START_GROUP = translate("Start group")

    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate("Import persons from table (clipboard)"))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(True)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.REPLACEMENT_BY_BIB = translate("Replacement by bib")
        self.REPLACEMENT_BY_NAME = translate("Replacement by name")
        self.INSERT_NEW = translate("Insert new records")

        self.option_import = AdvComboBox()
        self.option_import.addItems(
            [self.INSERT_NEW, self.REPLACEMENT_BY_BIB, self.REPLACEMENT_BY_NAME]
        )
        self.layout.addRow(self.option_import)

        self.headers = self.HEADER.list()

        copied_values = self.parse_clipboard_value()

        self.count_rows = len(copied_values)
        self.count_columns = len(copied_values[0]) if len(copied_values) else 0

        self.persons_info_table = QTableWidget(self)
        self.persons_info_table.setRowCount(self.count_rows)
        self.persons_info_table.setColumnCount(self.count_columns)

        for i in range(self.count_columns):
            header_import = AdvComboBox()
            header_import.addItems(self.headers)
            self.persons_info_table.setCellWidget(0, i, header_import)

        for idRow, row in enumerate(copied_values):
            for idColumn, cell in enumerate(row):
                new_item = QTableWidgetItem(cell)
                self.persons_info_table.setItem(idRow + 1, idColumn, new_item)

        self.layout.addRow(self.persons_info_table)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(e)
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(translate("OK"))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate("Cancel"))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.resize(900, 300)
        self.show()

    def apply_changes_impl(self):
        self.import_data()
        return

    @staticmethod
    def parse_clipboard_value():
        text = QApplication.clipboard().text()
        output_list = []
        for row in filter(None, text.splitlines()):
            output_list.append(row.split("\t"))
        return output_list

    def import_data(self):
        obj = memory.race()
        self.input_headers = {}
        for i in range(self.count_columns):
            item = self.persons_info_table.cellWidget(0, i)
            self.input_headers[self.HEADER(item.currentText())] = i

        for i in range(1, self.count_rows):
            person: memory.Person = None
            if self.option_import.currentText() == self.INSERT_NEW:
                person = memory.Person()

            if self.option_import.currentText() == self.REPLACEMENT_BY_BIB:
                if self.HEADER.BIB not in self.input_headers:
                    logging.error("{}".format(translate("Bib header not found")))
                    break
                bib = self.get_value_table(i, self.HEADER.BIB)
                if not bib.isdigit():
                    logging.error("{}".format(translate("Bib not found") + ":" + bib))
                    continue
                person = memory.race().find_person_by_bib(int(bib))
                if person is None:
                    logging.error("{}".format(translate("Bib not found") + ":" + bib))
                    continue

            if self.option_import.currentText() == self.REPLACEMENT_BY_NAME:
                if (self.HEADER.NAME not in self.input_headers) or (
                    self.HEADER.SURNAME not in self.input_headers
                ):
                    logging.error("{}".format(translate("Name header not found")))
                    break
                name = self.get_value_table(i, self.HEADER.NAME)
                surname = self.get_value_table(i, self.HEADER.SURNAME)
                person = find(race().persons, name=name, surname=surname)
                if person is None:
                    logging.error(
                        "{}".format(
                            translate("Person not found") + ":" + name + " " + surname
                        )
                    )
                    continue

            if self.HEADER.NAME in self.input_headers:
                person.name = self.get_value_table(i, self.HEADER.NAME)

            if self.HEADER.SURNAME in self.input_headers:
                person.surname = self.get_value_table(i, self.HEADER.SURNAME)

            if self.HEADER.YEAR in self.input_headers:
                year = self.get_value_table(i, self.HEADER.YEAR)
                if year.isdigit():
                    person.set_year(int(self.get_value_table(i, self.HEADER.YEAR)))

            if self.HEADER.GROUP in self.input_headers:
                group_name = self.get_value_table(i, self.HEADER.GROUP)
                group = memory.find(obj.groups, name=group_name)
                if group is None:
                    group = memory.Group()
                    group.name = group_name
                    group.long_name = group_name
                    obj.groups.append(group)
                person.group = group

            if self.HEADER.TEAM in self.input_headers:
                team_name = self.get_value_table(i, self.HEADER.TEAM)
                org = memory.find(obj.organizations, name=team_name)
                if org is None:
                    org = memory.Organization()
                    org.name = team_name
                    obj.organizations.append(org)
                person.organization = org

            if self.HEADER.BIB in self.input_headers:
                bib = self.get_value_table(i, self.HEADER.BIB)
                if bib != "":
                    set_property(person, self.HEADER.BIB.value, bib)

            if self.HEADER.CARD in self.input_headers:
                card = self.get_value_table(i, self.HEADER.CARD)
                if card != "":
                    set_property(person, self.HEADER.CARD.value, card)

            if self.HEADER.QUAL in self.input_headers:
                qual = self.get_value_table(i, self.HEADER.QUAL)
                if qual != "":
                    set_property(person, self.HEADER.QUAL.value, qual)

            if self.HEADER.COMMENT in self.input_headers:
                set_property(
                    person,
                    self.HEADER.COMMENT.value,
                    self.get_value_table(i, self.HEADER.COMMENT),
                )

            if self.HEADER.START in self.input_headers:
                set_property(
                    person,
                    self.HEADER.START.value,
                    self.get_value_table(i, self.HEADER.START),
                )

            if self.HEADER.FINISH in self.input_headers:
                set_property(
                    person,
                    self.HEADER.FINISH.value,
                    self.get_value_table(i, self.HEADER.FINISH),
                )

            if self.HEADER.START_GROUP in self.input_headers:
                set_property(
                    person,
                    self.HEADER.START_GROUP.value,
                    self.get_value_table(i, self.HEADER.START_GROUP),
                )

            if self.HEADER.MIDDLE_NAME in self.input_headers:
                person.middle_name = self.get_value_table(i, self.HEADER.MIDDLE_NAME)

            if self.HEADER.BIRTHDAY in self.input_headers:
                birthday = self.get_value_table(i, self.HEADER.BIRTHDAY)
                if birthday != "":
                    person.birth_date = ddmmyyyy_to_time(birthday)

            if self.option_import.currentText() == self.INSERT_NEW and person:
                obj.persons.append(person)

        persons_dupl_cards = obj.get_duplicate_card_numbers()
        persons_dupl_names = obj.get_duplicate_names()

        if len(persons_dupl_cards):
            logging.info(
                "{}".format(
                    translate("Duplicate card numbers (card numbers are reset)")
                )
            )
            for person in sorted(persons_dupl_cards, key=lambda x: x.card_number):
                logging.info(
                    "{} {} {} {}".format(
                        person.full_name,
                        person.group.name if person.group else "",
                        person.organization.name if person.organization else "",
                        person.card_number,
                    )
                )
                person.set_card_number(0)
        if len(persons_dupl_names):
            logging.info("{}".format(translate("Duplicate names")))
            for person in sorted(persons_dupl_names, key=lambda x: x.full_name):
                logging.info(
                    "{} {} {} {}".format(
                        person.full_name,
                        person.get_year(),
                        person.group.name if person.group else "",
                        person.organization.name if person.organization else "",
                    )
                )

    def get_value_table(self, idx, header):
        return (
            self.persons_info_table.item(idx, self.input_headers[header]).text().strip()
        )
