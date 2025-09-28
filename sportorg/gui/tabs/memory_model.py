import logging
import re
import uuid
from abc import abstractmethod
from copy import copy, deepcopy
from typing import List

from sportorg.gui.global_access import GlobalAccess

try:
    from PySide6.QtCore import QAbstractTableModel, Qt
except ModuleNotFoundError:
    from PySide2.QtCore import QAbstractTableModel, Qt

from sportorg import settings
from sportorg.language import translate
from sportorg.models.constant import RentCards
from sportorg.models.memory import (
    Course,
    Group,
    Organization,
    Person,
    Race,
    Result,
    race,
)
from sportorg.utils.time import time_to_hhmmss


class AbstractSportOrgMemoryModel(QAbstractTableModel):
    """
    Used to specify common table behavior
    """

    def __init__(self):
        super().__init__()
        self.race: Race = race()
        self.cache = []
        self.init_cache()
        self.filter = {}
        self.r_count = 0
        self.max_rows_count = 5000
        self.c_count = len(self.get_headers())

        # temporary list, used to keep records, that are not filtered
        # main list will have only filtered elements
        # while clearing of filter list is recovered from backup
        self.filter_backup = []

        self.search = ""
        self.search_old = ""
        self.search_offset = 0

    @abstractmethod
    def init_cache(self):
        pass

    @abstractmethod
    def get_values_from_object(self, obj):
        pass

    @abstractmethod
    def get_source_array(self) -> List:
        pass

    @abstractmethod
    def set_source_array(self, array):
        pass

    @abstractmethod
    def get_headers(self) -> List:
        pass

    @abstractmethod
    def get_data(self, position):
        pass

    @abstractmethod
    def duplicate(self, position):
        pass

    def columnCount(self, parent=None, *args, **kwargs):
        return self.c_count

    def rowCount(self, parent=None, *args, **kwargs):
        return min(len(self.cache), self.max_rows_count)

    def headerData(self, index, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                columns = self.get_headers()
                return columns[index]
            if orientation == Qt.Vertical:
                return str(index + 1)

    def data(self, index, role=None):
        if role == Qt.DisplayRole:
            try:
                row = index.row()
                column = index.column()
                answer = self.cache[row][column]
                return answer
            except Exception as e:
                logging.error(str(e))
        return

    def clear_filter(self, remove_condition=True):
        if remove_condition:
            self.filter.clear()
        if self.filter_backup and len(self.filter_backup):
            whole_list = self.get_source_array()
            whole_list.extend(self.filter_backup)
            self.set_source_array(whole_list)
            self.filter_backup.clear()

    def set_filter_for_column(self, column_num, filter_regexp, action):
        self.filter.update({column_num: [filter_regexp, action]})

    def apply_filter(self):
        # get initial list and filter it
        current_array = self.get_source_array()
        current_array.extend(self.filter_backup)
        self.filter_backup.clear()
        for column in self.filter.keys():
            filter_action = self.filter.get(column)[1]
            filter_value = self.filter.get(column)[0]

            check = self.compile_regex(filter_action, filter_value)

            i = 0
            while i < len(current_array):
                value = self.get_item(current_array[i], column)
                if not self.match_value(check, str(value)):
                    self.filter_backup.append(current_array.pop(i))
                    i -= 1
                i += 1

        # set main list to result
        # note, unfiltered items are in filter_backup
        self.set_source_array(current_array)
        self.init_cache()

    @staticmethod
    def compile_regex(action: str, raw_value: str) -> re.Pattern:
        """Compiles a regular expression pattern based on filter action filter value.

        Args:
            action (str): The action to perform (contain, equal to, doesn't contain).
            raw_value (str): The filter value to match against.

        Returns:
            Pattern[str]: The compiled regular expression pattern.
        """
        value = re.escape(raw_value)
        regex_string = {
            translate("contain"): f".*{value}.*",
            translate("equal to"): f"{value}$",
            translate("doesn't contain"): f"^((?!{value}).)*$",
            translate("in list"): f"{value.replace(',', '|')}$",
        }.get(action, ".*")
        return re.compile(regex_string)

    @staticmethod
    def match_value(check: re.Pattern, value: str) -> bool:
        return bool(check.match(value))

    def apply_search(self):
        if not self.search:
            return
        if self.search != self.search_old:
            self.search_offset = 0
        else:
            self.search_offset += 1
        current_array = self.get_source_array()
        escaped_text = re.escape(self.search)
        check = re.compile(escaped_text, re.IGNORECASE)

        count_columns = len(self.get_headers())
        columns = range(count_columns)

        # 1 phase - full match
        i = 0
        maximum = len(current_array)
        while i < maximum:
            cur_pos = (self.search_offset + i) % maximum
            obj = current_array[cur_pos]
            row_values = self.get_values_from_object(obj)
            row_values.append(self._extract_bib(obj))  # add raw bib to search
            row_values.append(self._extract_relay_bib(obj).replace(".", ","))
            for value in [str(v) for v in row_values]:
                if value == self.search:
                    self.search_offset = cur_pos
                    self.search_old = self.search
                    return
            i += 1

        # 2 phase - match
        i = 0
        maximum = len(current_array)
        while i < maximum:
            cur_pos = (self.search_offset + i) % maximum
            row_values = self.get_values_from_object(current_array[cur_pos])
            for column in columns:
                value = str(row_values[column])
                if check.match(value):
                    self.search_offset = cur_pos
                    self.search_old = self.search
                    return
            i += 1

        # 3 phase - search
        i = 0
        maximum = len(current_array)
        while i < maximum:
            cur_pos = (self.search_offset + i) % maximum
            row_values = self.get_values_from_object(current_array[cur_pos])
            for column in columns:
                value = str(row_values[column])
                if check.search(value):
                    self.search_offset = cur_pos
                    self.search_old = self.search
                    return
            i += 1

        self.search_offset = -1

    def _extract_bib(self, obj) -> str:
        """
        Extracts the bib number as a string from a given object or returns an empty string if not available
        """
        bib = ""
        if isinstance(obj, Person):
            bib = str(obj.bib)
        elif isinstance(obj, Result):
            bib = str(obj.person.bib) if obj.person else ""
        return bib

    def _extract_relay_bib(self, obj) -> str:
        """
        Extracts the rey bib number as a string from a given object or returns an empty string if not available
        """
        bib = ""
        if isinstance(obj, Person):
            bib = str(obj.get_relay_bib())
        elif isinstance(obj, Result):
            bib = str(obj.person.get_relay_bib()) if obj.person else ""
        return bib

    def sort(self, p_int, order=None):
        """Sort table by given column number."""

        def default_sort_key(x):
            item = self.get_item(x, p_int)
            return item is None, str(type(item)), item

        def birthday_sort_key(person: Person):
            return person.birth_date is None, person.birth_date

        def bib_persons_sort_key(person: Person):
            return (
                person.bib is None,
                person.get_relay_team_number() or person.bib,
                person.get_relay_leg_number(),
            )

        def bib_results_sort_key(result: Result):
            if result.person is None:
                return (True, 0, 0)
            person = result.person
            return (
                person.bib is None,
                person.get_relay_team_number() or person.bib,
                person.get_relay_leg_number(),
            )

        current_tab = GlobalAccess().get_main_window().current_tab
        sort_key = default_sort_key
        if self.get_headers()[p_int] == translate("Birthday title"):
            sort_key = birthday_sort_key
        elif self.get_headers()[p_int] == translate("Bib") and current_tab == 0:
            sort_key = bib_persons_sort_key
        elif self.get_headers()[p_int] == translate("Bib") and current_tab == 1:
            sort_key = bib_results_sort_key

        try:
            is_descending = order == Qt.DescendingOrder
            self.layoutAboutToBeChanged.emit()

            source_array = self.get_source_array()

            if len(source_array):
                source_array = sorted(source_array, key=sort_key, reverse=is_descending)

                self.set_source_array(source_array)

                self.init_cache()
            self.layoutChanged.emit()
        except Exception as e:
            logging.error(str(e))

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)

    def get_item(self, obj, n_col):
        return self.get_values_from_object(obj)[n_col]

    def get_column_unique_values(self, n_col):
        # returns sorted unique values from specified column
        return sorted(set([str(row[n_col]) for row in self.cache]))


class PersonMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.init_cache()

    def get_headers(self) -> List[str]:
        use_birthday = settings.SETTINGS.race_use_birthday

        return [
            translate("Last name"),
            translate("First name"),
            translate("Middle name"),
            translate("Qualification title"),
            translate("Group"),
            translate("Team"),
            translate("Birthday title") if use_birthday else translate("Year title"),
            translate("Bib"),
            translate("Start"),
            translate("Start group"),
            translate("Card title"),
            translate("Rented card"),
            translate("Comment"),
            translate("World code title"),
            translate("National code title"),
            translate("Out of competition title"),
            translate("Course"),
            translate("Max time at"),
            translate("Result count title"),
        ]

    def init_cache(self):
        self.cache.clear()
        for row in range(len(self.race.persons)):
            self.cache.append(self.get_data(row))

    def get_data(self, position: int):
        return self.get_values_from_object(self.race.persons[position])

    def duplicate(self, position):
        person = self.race.persons[position]
        new_person = copy(person)
        new_person.id = uuid.uuid4()
        new_person.set_bib_without_indexing(0)
        new_person.set_card_number_without_indexing(0)
        self.race.persons.insert(position, new_person)

    def get_values_from_object(self, person: Person):
        ret = []

        is_rented_card = person.is_rented_card or RentCards().exists(person.card_number)
        rented_card_text = (
            translate("Rented card") if is_rented_card else translate("Rented stub")
        )

        use_birthday = settings.SETTINGS.race_use_birthday

        start_source = race().get_setting("system_start_source", "protocol")
        max_time_ends_at_str = ""
        if (
            person.group
            and person.group.max_time
            and person.start_time
            and not person.result_count
            and start_source == "protocol"
        ):
            max_time_at = person.start_time + person.group.max_time
            max_time_ends_at_str = max_time_at.to_str()

        ret = [
            person.surname,
            person.name,
            person.middle_name,
            person.qual.get_title() if person.qual else "",
            person.group.name if person.group else "",
            person.organization.name if person.organization else "",
            person.get_birthday() if use_birthday else person.year,
            person.get_relay_bib() or person.bib,
            person.start_time.to_str(),
            person.start_group,
            person.card_number,
            rented_card_text,
            person.comment,
            str(person.world_code) if person.world_code else "",
            str(person.national_code) if person.national_code else "",
            translate("o/c") if person.is_out_of_competition else "",
            person.group.course.name if (person.group and person.group.course) else "",
            max_time_ends_at_str,
            person.result_count,
        ]

        return ret

    def get_source_array(self):
        return self.race.persons

    def set_source_array(self, array):
        self.race.persons = array


class ResultMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.values = None
        self.count = None

    def get_headers(self) -> List[str]:
        return [
            translate("Last name"),
            translate("First name"),
            translate("Group"),
            translate("Team"),
            translate("Place"),
            translate("Result"),
            translate("Diff"),
            translate("Status"),
            translate("Bib"),
            translate("Card title"),
            translate("Start"),
            translate("Finish"),
            translate("Credit"),
            translate("Penalty"),
            translate("Penalty legs title"),
            translate("Type"),
            translate("Rented card"),
            translate("Result day/leg"),
            translate("Comment"),
        ]

    def init_cache(self):
        self.cache.clear()
        for row in range(len(self.race.results)):
            self.cache.append(self.get_data(row))

    def get_data(self, position):
        ret = self.get_values_from_object(self.race.results[position])
        return ret

    def duplicate(self, position):
        result = self.race.results[position]
        new_result = copy(result)
        new_result.id = uuid.uuid4()
        new_result.splits = deepcopy(result.splits)
        self.race.results.insert(position, new_result)

    def get_values_from_object(self, result: Result):
        person = result.person if result.person is not None else Person()

        is_rented_card = person.is_rented_card or RentCards().exists(result.card_number)
        rented_card_text = (
            translate("Rented card") if is_rented_card else translate("Rented stub")
        )

        time_accuracy = self.race.get_setting("time_accuracy", 0)
        start = ""
        if result.get_start_time():
            start = result.get_start_time().to_str(time_accuracy)
        finish = ""
        if result.get_finish_time():
            finish = result.get_finish_time().to_str(time_accuracy)
        day_leg_result = (
            result.get_result_otime_current_day().to_str(time_accuracy)
            if result.is_status_ok()
            else result.get_result()
        )

        ret = [
            person.surname,
            person.name,
            person.group.name if person.group else "",
            person.organization.name if person.organization else "",
            result.get_place(),
            result.get_result(),
            result.diff.to_str() if result.diff else "",
            result.status.get_title(),
            person.get_relay_bib() or person.bib,
            result.card_number,
            start,
            finish,
            result.get_credit_time().to_str() if result.get_credit_time() else "",
            result.get_penalty_time().to_str() if result.get_penalty_time() else "",
            result.penalty_laps,
            str(result.system_type),
            rented_card_text,
            day_leg_result,
            person.comment,
        ]
        return ret

    def get_source_array(self):
        return self.race.results

    def set_source_array(self, array):
        self.race.results = array


class GroupMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()

    def get_headers(self) -> List[str]:
        return [
            translate("Name"),
            translate("Full name"),
            translate("Course name"),
            translate("Start fee title"),
            translate("Type"),
            translate("Length title"),
            translate("Point count title"),
            translate("Climb title"),
            translate("Min year title"),
            translate("Max year title"),
            translate("Max time title"),
            translate("Start corridor title"),
            translate("Order in corridor title"),
            translate("Start interval title"),
            translate("Count of person"),
            translate("Count of finished"),
            translate("Count of not finished"),
        ]

    def init_cache(self):
        self.cache.clear()
        for row in range(len(self.race.groups)):
            self.cache.append(self.get_data(row))

    def get_data(self, position):
        ret = self.get_values_from_object(self.race.groups[position])
        return ret

    def duplicate(self, position):
        group = self.race.groups[position]
        new_group = copy(group)
        new_group.id = uuid.uuid4()
        new_group.name = new_group.name + "_"
        self.race.groups.insert(position, new_group)

    def get_values_from_object(self, group: Group):
        course = group.course

        control_count = len(course.controls) if course else 0

        return [
            group.name,
            group.long_name,
            course.name if course else "",
            group.price,
            self.race.get_type(group).get_title(),
            course.length if course else 0,
            control_count,
            course.climb if course else 0,
            group.min_year,
            group.max_year,
            group.max_time.to_str() if group.max_time else "",
            group.start_corridor,
            group.order_in_corridor,
            group.start_interval.to_str() if group.start_interval else "",
            group.count_person,
            group.count_finished,
            group.count_person - group.count_finished,
        ]

    def get_source_array(self):
        return self.race.groups

    def set_source_array(self, array):
        self.race.groups = array


class CourseMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()

    def get_headers(self) -> List[str]:
        return [
            translate("Name"),
            translate("Length title"),
            translate("Point count title"),
            translate("Climb title"),
            translate("Controls"),
            translate("Count of person"),
            translate("Count of finished"),
            translate("Count of not finished"),
            translate("Count of groups"),
        ]

    def init_cache(self):
        self.cache.clear()
        for row in range(len(self.race.courses)):
            self.cache.append(self.get_data(row))

    def get_data(self, position):
        ret = self.get_values_from_object(self.race.courses[position])
        return ret

    def duplicate(self, position):
        course = self.race.courses[position]
        old_name = course.name
        new_course = copy(course)
        new_course.id = uuid.uuid4()
        new_name = course.name + "_"
        while new_name in self.race.course_index_name:
            new_name = new_name + "_"
        new_course.name = new_name
        course.name = (
            old_name  # recover index for old name, broken while setting name to copy
        )
        new_course.controls = deepcopy(course.controls)
        self.race.courses.insert(position, new_course)

    def get_values_from_object(self, course: Course):
        return [
            course.name,
            course.length,
            len(course.controls),
            course.climb,
            " ".join(course.get_code_list()),
            course.count_person,
            course.count_finished,
            course.count_person - course.count_finished,
            course.count_group,
        ]

    def get_source_array(self):
        return self.race.courses

    def set_source_array(self, array):
        self.race.courses = array


class OrganizationMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()

    def get_headers(self) -> List[str]:
        return [
            translate("Name"),
            translate("Code"),
            translate("Country"),
            translate("Region"),
            translate("Contact"),
            translate("Count of person"),
            translate("Count of finished"),
            translate("Count of not finished"),
        ]

    def init_cache(self):
        self.cache.clear()
        for row in range(len(self.race.organizations)):
            self.cache.append(self.get_data(row))

    def get_data(self, position):
        ret = self.get_values_from_object(self.race.organizations[position])
        return ret

    def duplicate(self, position):
        organization = self.race.organizations[position]
        new_organization = copy(organization)
        new_organization.id = uuid.uuid4()
        new_organization.name = new_organization.name + "_"
        self.race.organizations.insert(position, new_organization)

    def get_values_from_object(self, organization: Organization):
        return [
            organization.name,
            organization.code,
            organization.country,
            organization.region,
            organization.contact,
            organization.count_person,
            organization.count_finished,
            organization.count_person - organization.count_finished,
        ]

    def get_source_array(self):
        return self.race.organizations

    def set_source_array(self, array):
        self.race.organizations = array
