from datetime import date

from sportorg.gui.dialogs.dialog import (
    AdvComboBoxField,
    BaseDialog,
    CheckBoxField,
    DateField,
    LabelField,
    LineField,
    NumberField,
    TextField,
    TimeField,
)
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.constant import get_names, get_race_groups, get_race_teams
from sportorg.models.memory import Limit, Organization, Qualification, find, race
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.modules.configs.configs import Config


class PersonEditDialog(BaseDialog):
    GROUP_NAME = ''
    ORGANIZATION_NAME = ''

    def __init__(self, person, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        self.current_object = person
        self.is_new = is_new
        self.is_item_valid = {}

        time_format = 'hh:mm:ss'
        if race().get_setting('time_accuracy', 0):
            time_format = 'hh:mm:ss.zzz'

        self.title = translate('Entry properties')
        self.size = (450, 640)
        self.form = [
            LineField(
                title=translate('Last name'),
                object=person,
                key='surname',
                select_all=True,
            ),
            AdvComboBoxField(
                title=translate('First name'),
                object=person,
                key='name',
                items=get_names(),
            ),
            AdvComboBoxField(
                title=translate('Group'),
                object=person,
                key='group',
                id='group',
                items=get_race_groups(),
            ),
            LabelField(id='group_info'),
            AdvComboBoxField(
                title=translate('Team'),
                object=person,
                key='organization',
                id='organization',
                items=get_race_teams(),
            ),
            DateField(
                title=translate('Birthday'),
                object=person,
                key='birth_date',
                maximum=date.today(),
            )
            if Config().configuration.get('use_birthday', False)
            else NumberField(
                title=translate('Year of birth'),
                object=person,
                key='year',
                id='year',
                minimum=0,
                maximum=date.today().year,
            ),
            AdvComboBoxField(
                title=translate('Qualification'),
                object=person,
                key='qual',
                id='qual',
                items=[qual.get_title() for qual in Qualification],
            ),
            NumberField(
                title=translate('Bib'),
                object=person,
                key='bib',
                id='bib',
                minimum=0,
                maximum=Limit.BIB,
            ),
            LabelField(id='bib_info'),
            LineField(
                title=translate('World code'),
                object=person,
                key='world_code',
            ),
            LineField(
                title=translate('National code'),
                object=person,
                key='national_code',
            ),
            TimeField(
                title=translate('Start time'),
                object=person,
                key='start_time',
                format=time_format,
            ),
            NumberField(
                title=translate('Start group'),
                object=person,
                key='start_group',
                minimum=0,
                maximum=99,
            ),
            NumberField(
                title=translate('Punch card #'),
                object=person,
                key='card_number',
                id='card_number',
                minimum=0,
                maximum=9999999,
            ),
            LabelField(id='card_info'),
            CheckBoxField(
                label=translate('rented card'),
                object=person,
                key='is_rented_card',
            ),
            CheckBoxField(
                label=translate('is paid'),
                object=person,
                key='is_paid',
            ),
            CheckBoxField(
                label=translate('personal participation'),
                object=person,
                key='is_personal',
            ),
            CheckBoxField(
                label=translate('out of competition'),
                object=person,
                key='is_out_of_competition',
            ),
            TextField(
                title=translate('Comment'),
                object=person,
                key='comment',
            ),
        ]

    def convert_group(self, group) -> str:
        if not group:
            return self.GROUP_NAME
        return group.name

    def convert_organization(self, organization) -> str:
        if not organization:
            return self.ORGANIZATION_NAME
        return organization.name

    def convert_qual(self, qual) -> str:
        return qual.get_title()

    def parse_group(self, text: str):
        return find(race().groups, name=text)

    def parse_organization(self, text: str):
        organization = find(race().organizations, name=text)
        if not organization:
            organization = Organization()
            organization.name = text
            race().organizations.append(organization)
        return organization

    def parse_qual(self, text: str):
        return Qualification.get_qual_by_name(text)

    def on_year_finished(self):
        """
        Convert 2 digits of year to 4
        2 -> 2002
        11 -> 2011
        33 -> 1933
        56 -> 1956
        98 -> 1998
        0 -> 0 exception!
        """
        widget = self.sender()
        year = widget.value()
        if 0 < year < 100:
            cur_year = date.today().year
            new_year = cur_year - cur_year % 100 + year
            if new_year > cur_year:
                new_year -= 100
            widget.setValue(new_year)

    def is_items_ok(self):
        values = self.is_item_valid.values()
        return sum(values) == len(values)

    def on_group_changed(self):
        self.is_item_valid['group'] = True
        group_name = self.fields['group'].q_item.currentText()
        group_info = self.fields['group_info']
        group_info.set_text('')
        if group_name and not find(race().groups, name=group_name):
            self.is_item_valid['group'] = False
            group_info.set_text(translate('Group not found'))

        self.button_ok.setEnabled(self.is_items_ok())

    def on_bib_changed(self):
        self.is_item_valid['bib'] = True
        bib = self.fields['bib'].q_item.value()
        bib_info = self.fields['bib_info']
        bib_info.set_text('')
        if bib:
            person = find(race().persons, bib=bib)
            if not person:
                bib_info.set_text(translate('Number is unique'))
            elif person is not self.current_object:
                self.is_item_valid['bib'] = False
                info = '{}\n{}'.format(
                    translate('Number already exists'), person.full_name
                )
                if person.group:
                    info = '{}\n{}: {}'.format(
                        info, translate('Group'), person.group.name
                    )
                bib_info.set_text(info)
        self.button_ok.setEnabled(self.is_items_ok())

    def on_card_number_changed(self):
        self.is_item_valid['card_number'] = True
        number = self.fields['card_number'].q_item.value()
        card_info = self.fields['card_info']
        card_info.set_text('')
        if number:
            person = find(race().persons, card_number=number)
            if not person:
                card_info.set_text(translate('Card number is unique'))
            elif person is not self.current_object:
                self.is_item_valid['card_number'] = False
                info = '{}\n{}'.format(
                    translate('Card number already exists'), person.full_name
                )
                if person.group:
                    info = '{}\n{}: {}'.format(
                        info, translate('Group'), person.group.name
                    )
                if person.bib:
                    info = '{}\n{}: {}'.format(info, translate('Bib'), person.bib)
                card_info.set_text(info)
        self.button_ok.setEnabled(self.is_items_ok())

    def apply(self):
        person = self.current_object
        if self.is_new:
            race().persons.insert(0, person)

        ResultCalculation(race()).process_results()
