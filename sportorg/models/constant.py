import logging
import operator
from pathlib import Path
from typing import Dict, List, Set

from sportorg.common.singleton import singleton
from sportorg import settings
from sportorg.models.memory import Qualification, ResultStatus, race


def _read_config_items(path: str) -> List[str]:
    try:
        with Path(path).open(encoding="utf-8") as f:
            return [x.strip() for x in f.readlines()]
    except Exception as e:
        logging.exception(str(e))
        return []


def _normalize_first_empty(items: List[str]) -> List[str]:
    return [""] + [str(x).strip() for x in items if str(x).strip()]


def get_countries():
    return Countries().get_all()


def get_regions():
    return Regions().get_all()


def get_groups():
    return Groups().get_all()


def get_race_groups():
    ret = [""]
    try:
        for i in race().groups:
            if i.name:
                ret.append(i.name)
        return ret
    except Exception as e:
        logging.error(str(e))
        return get_groups()


def get_teams():
    return [""]


def get_race_teams():
    ret = [""]
    try:
        for i in race().organizations:
            if i.name:
                ret.append(i.name)
        return ret
    except Exception as e:
        logging.error(str(e))
        return get_teams()


def get_race_courses():
    ret = [""]
    try:
        for i in race().courses:
            if i.name:
                ret.append(i.name)
        return ret
    except Exception as e:
        logging.error(str(e))
        return []


def get_names():
    return PersonNames().get_all()


def get_middle_names():
    return PersonMiddleNames().get_all()


def get_qualification_list():
    return [q.get_title() for q in Qualification]


@singleton
class Countries:
    COUNTRIES: List[str] = []
    _LOADED = False

    def get_all(self):
        if not self._LOADED:
            self.set(_read_config_items(settings.SETTINGS.source_countries_path))
        return self.COUNTRIES

    def set(self, items):
        self.COUNTRIES = _normalize_first_empty(items)
        self._LOADED = True


@singleton
class Groups:
    GROUPS: List[str] = []
    _LOADED = False

    def get_all(self):
        if not self._LOADED:
            self.set(_read_config_items(settings.SETTINGS.source_groups_path))
        return self.GROUPS

    def set(self, items):
        self.GROUPS = _normalize_first_empty(items)
        self._LOADED = True


@singleton
class PersonNames:
    NAMES: List[str] = []

    def get_all(self):
        return self.NAMES

    def set(self, items):
        items.sort()
        if "" not in items:
            items.insert(0, "")
        self.NAMES = items


@singleton
class PersonMiddleNames:
    NAMES: List[str] = []

    def get_all(self):
        return self.NAMES

    def set(self, items):
        items.sort()
        if "" not in items:
            items.insert(0, "")
        self.NAMES = items


@singleton
class Regions:
    REGIONS: List[str] = []

    def get_all(self):
        return self.REGIONS

    def set(self, items):
        items.sort()
        if "" not in items:
            items.insert(0, "")
        self.REGIONS = items


@singleton
class StatusComments:
    STATUS_COMMENTS: List[str] = []
    DEFAULT_STATUSES: Dict[str, str] = {}

    def get_all(self):
        return self.STATUS_COMMENTS

    def get(self):
        for item in self.STATUS_COMMENTS:
            if item:
                return item
        return ""

    def set(self, items):
        if "" not in items:
            items.insert(0, "")
        self.STATUS_COMMENTS = items

    @staticmethod
    def remove_hint(full_str):
        return str(full_str).split("#")[0].strip()

    def set_default_statuses(self, items):
        for cur_item in items:
            code = cur_item.split("=")[0].strip()
            value = cur_item.split("=")[1].strip()
            self.DEFAULT_STATUSES[code] = value

    def get_status_default_comment(self, status: ResultStatus) -> str:
        if status.name in self.DEFAULT_STATUSES:
            return self.DEFAULT_STATUSES[status.name]
        return ""


@singleton
class RentCards:
    CARDS: Set[int] = set()

    def exists(self, item):
        return item in self.CARDS

    def append(self, *items):
        for item in items:
            self.CARDS.add(item)

    def set(self, items):
        self.CARDS = set(items)

    def get(self):
        return self.CARDS

    def set_from_text(self, text, separator="\n"):
        self.CARDS = set()
        for item in text.split(separator):
            if not len(item):
                continue
            for n_item in item.split():
                if n_item.isdigit():
                    self.append(int(n_item))

    def to_text(self, separator="\n"):
        return separator.join([str(x) for x in self.CARDS])


@singleton
class RankingTable:
    """
    Ranking is read from configuration file called 'ranking.txt' / 'ranking_ardf.txt'
    ```
    Format: RANK;I;II;III;I_Y;II_Y[;III_Y[;KMS[;MS]]]
    e.g. 1000;136;151;169;;
    e.g. 850;133;148;166;;
    e.g. 5;;;;;100
    ```
    """

    _RANKING_TABLES = {}

    _current_type = "default"

    column_mapping = {
        Qualification.I: 1,
        Qualification.II: 2,
        Qualification.III: 3,
        Qualification.I_Y: 4,
        Qualification.II_Y: 5,
        Qualification.III_Y: 6,
        Qualification.KMS: 7,
        Qualification.MS: 8,
    }

    @classmethod
    def set_current_type(cls, table_type: str):
        cls._current_type = table_type

    @classmethod
    def get_table(cls, table_type: str = None):
        table_type = table_type or cls._current_type
        return cls._RANKING_TABLES.get(table_type, [])

    @classmethod
    def set_table(cls, items, table_type: str = "default"):
        table_data = []
        for i in items:
            row = []
            for j in i:
                if str(j).isdecimal():
                    row.append(int(j))
                else:
                    row.append(0)
            table_data.append(row)

        cls._RANKING_TABLES[table_type] = table_data

    def get_all(self):
        return self.get_table(self._current_type)

    def get_qual_table(self, qual):
        # get only 2 columns from whole table, corresponding to specified qualification
        try:
            table_data = self.get_table(self._current_type)
            columns = [0, self.column_mapping[qual]]
            my_items = operator.itemgetter(*columns)
            return [my_items(x) for x in table_data]
        except Exception:
            # logging.exception(e)
            return [[0, 0]]
