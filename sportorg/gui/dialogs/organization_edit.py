from sportorg.gui.dialogs.dialog import AdvComboBoxField, BaseDialog, LineField
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.constant import get_countries, get_regions
from sportorg.models.memory import find, race


class OrganizationEditDialog(BaseDialog):
    def __init__(self, organization, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        self.current_object = organization
        self.is_new = is_new
        self.title = translate('Team properties')
        self.size = (600, 250)
        self.form = [
            LineField(
                title=translate('Name'),
                object=organization,
                key='name',
                id='name',
                select_all=True,
            ),
            LineField(
                title=translate('Code'),
                object=organization,
                key='code',
            ),
            AdvComboBoxField(
                title=translate('Country'),
                object=organization,
                key='country',
                items=get_countries(),
            ),
            AdvComboBoxField(
                title=translate('Region'),
                object=organization,
                key='region',
                items=get_regions(),
            ),
            LineField(
                title=translate('Contact'),
                object=organization,
                key='contact',
            ),
        ]

    def on_name_changed(self):
        name = self.fields['name'].q_item.text()
        self.button_ok.setDisabled(False)
        if name and name != self.current_object.name:
            org = find(race().organizations, name=name)
            if org:
                self.button_ok.setDisabled(True)

    def apply(self):
        org = self.current_object
        if self.is_new:
            race().organizations.insert(0, org)
