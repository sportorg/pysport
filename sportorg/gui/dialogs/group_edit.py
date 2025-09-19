from datetime import date

from sportorg.gui.dialogs.dialog import (
    AdvComboBoxField,
    BaseDialog,
    ButtonField,
    CheckBoxField,
    LineField,
    NumberField,
    TimeField,
)
from sportorg.gui.dialogs.group_ranking import GroupRankingDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.constant import get_race_courses
from sportorg.models.memory import Limit, RaceType, find, race
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.modules.live.live import live_client
from sportorg.modules.teamwork.teamwork import Teamwork

ALL_RUSSIAN_COMPETITION_TOOLTIP = """Sequence of results in regular competitions:
1) Relay teams with results (including teams from different organizations, out of competition teams)
2) Incomplete teams with results
3) Complete disqualified teams
4) Incomplete disqualified teams

Sequence of results in all-Russian competitions:
1) Relay teams, all participants from the same organization
2) Relay teams, participants from different organizations
3) Relay teams, out of competition
4) Incomplete teams with results
5) Complete disqualified teams
6) Incomplete disqualified teams"""

BEST_TEAM_PLACING_TOOLTIP = """Sequence of results taking into account the international principle:
1) Relay teams, all participants from the same organization, one team per organization
2) Relay teams, all participants from one organization, other teams from organizations
3) Relay teams, participants from different organizations
4) Relay teams, out of competition
5) Incomplete teams with results
6) Complete disqualified teams
7) Incomplete disqualified teams"""


class GroupEditDialog(BaseDialog):
    def __init__(self, group, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        self.current_object = group
        self.is_new = is_new
        time_format = "hh:mm:ss"
        self.title = translate("Group properties")
        self.size = (450, 540)
        self.form = [
            LineField(
                title=translate("Name"),
                object=group,
                key="name",
                id="name",
                select_all=True,
            ),
            LineField(
                title=translate("Full name"),
                object=group,
                key="long_name",
            ),
            AdvComboBoxField(
                title=translate("Course"),
                object=group,
                key="course",
                id="course",
                items=get_race_courses(),
            ),
            CheckBoxField(
                label=translate("Is any course"),
                object=group,
                key="is_any_course",
                id="is_any_course",
            ),
            NumberField(
                title=translate("Min year"),
                object=group,
                key="min_year",
                id="min_year",
                minimum=0,
                maximum=date.today().year,
            ),
            NumberField(
                title=translate("Max year"),
                object=group,
                key="max_year",
                id="max_year",
                minimum=0,
                maximum=date.today().year,
            ),
            TimeField(
                title=translate("Max time"),
                object=group,
                key="max_time",
                format=time_format,
            ),
            NumberField(
                title=translate("Start corridor"),
                object=group,
                key="start_corridor",
            ),
            NumberField(
                title=translate("Order in corridor"),
                object=group,
                key="order_in_corridor",
            ),
            TimeField(
                title=translate("Start interval"),
                object=group,
                key="start_interval",
                format=time_format,
            ),
            NumberField(
                title=translate("Start fee"),
                object=group,
                key="price",
                single_step=50,
                maximum=Limit.PRICE,
            ),
            AdvComboBoxField(
                title=translate("Type"),
                object=group,
                key="race_type",
                id="race_type",
                items=RaceType.get_titles(),
            ),
            CheckBoxField(
                label=translate("All-Russian competition") + " 🛈",
                object=group,
                key="is_all_russian_competition",
                id="is_all_russian_competition",
                tooltip=translate(ALL_RUSSIAN_COMPETITION_TOOLTIP),
            ),
            CheckBoxField(
                label=translate("Best team placing") + " 🛈",
                object=group,
                key="is_best_team_placing_mode",
                id="is_best_team_placing_mode",
                tooltip=translate(BEST_TEAM_PLACING_TOOLTIP),
            ),
            CheckBoxField(
                label=translate("Rank calculation"),
                object=group.ranking,
                key="is_active",
                id="is_ranking_active",
            ),
            ButtonField(text=translate("Configuration"), id="ranking"),
        ]

    def before_showing(self) -> None:
        self.on_is_any_course_changed()
        self.on_is_ranking_active_changed()
        self.on_race_type_changed()

    def convert_course(self, course) -> str:
        if not course:
            return ""
        return course.name

    def convert_race_type(self, _) -> str:
        return race().get_type(self.current_object).get_title()

    def parse_course(self, text: str):
        if text in race().course_index_name:
            return race().course_index_name[text]
        return find(race().courses, name=text)

    def parse_race_type(self, text: str):
        return RaceType.get_by_name(text)

    def is_relay_type_selected(self):
        race_type_text = self.fields["race_type"].q_item.currentText()
        return self.parse_race_type(race_type_text) == RaceType.RELAY

    def on_name_changed(self):
        name = self.fields["name"].q_item.text()
        self.button_ok.setDisabled(False)
        if name and name != self.current_object.name:
            group = find(race().groups, name=name)
            if group:
                self.button_ok.setDisabled(True)

    def on_ranking_clicked(self):
        GroupRankingDialog(self.current_object).exec_()

    def on_is_any_course_changed(self):
        self.fields["course"].q_item.setDisabled(
            self.fields["is_any_course"].q_item.isChecked()
        )

    def on_is_ranking_active_changed(self):
        self.fields["ranking"].q_item.setEnabled(
            self.fields["is_ranking_active"].q_item.isChecked()
        )

    def on_race_type_changed(self):
        competition_type_item = self.fields["is_all_russian_competition"].q_item
        best_placing_item = self.fields["is_best_team_placing_mode"].q_item
        if self.is_relay_type_selected():
            competition_type_item.show()
            best_placing_item.show()
        else:
            competition_type_item.hide()
            best_placing_item.hide()
        competition_type_item.stateChanged.connect(self.on_competition_type_changed)

    def on_competition_type_changed(self):
        is_all_russian = self.fields["is_all_russian_competition"].q_item.isChecked()
        self.fields["is_best_team_placing_mode"].q_item.setEnabled(is_all_russian)
        if not is_all_russian:
            self.fields["is_best_team_placing_mode"].q_item.setChecked(False)

    def on_min_year_finished(self):
        self.change_year()

    def on_max_year_finished(self):
        self.change_year()

    def change_year(self):
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

    def apply(self):
        group = self.current_object
        if self.is_new:
            race().groups.insert(0, group)

        ResultCalculation(race()).set_rank(group)
        live_client.send(group)
        Teamwork().send(group.to_dict())
