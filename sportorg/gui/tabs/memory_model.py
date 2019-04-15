import logging
import re
import uuid
from abc import abstractmethod
from copy import copy, deepcopy

from PySide2.QtCore import QModelIndex
from PySide2.QtCore import QAbstractTableModel, Qt
from typing import List

from sportorg.language import _
from sportorg.models.memory import race



class AbstractSportOrgMemoryModel(QAbstractTableModel):
    """
    Used to specify common table behavior
    """

    INITIAL_LOAD_QTY = 200000

    def __init__(self):
        super().__init__()
        self.race = race()
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

        self.search = ''
        self.search_old = ''
        self.search_offset = 0

        self.rows_loaded = self.INITIAL_LOAD_QTY

    @abstractmethod
    def get_values_from_object(self, obj):
        pass

    def get_source_array(self) -> List:
        return self.cache

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
        return self.c_count + 1

    def rowCount(self, parent=None, *args, **kwargs):
        return min(len(self.cache), self.rows_loaded)
        #return min(len(self.cache), self.max_rows_count)

    def canFetchMore(self, *args, **kwargs):
        if len(self.cache) > self.rows_loaded:
            return True
        else:
            return False

    def fetchMore(self, *args, **kwargs):
        reminder = len(self.cache) - self.rows_loaded
        itemsToFetch = min(reminder, self.INITIAL_LOAD_QTY)
        self.beginInsertRows(QModelIndex(), self.rows_loaded, self.rows_loaded + itemsToFetch - 1)
        self.rows_loaded += itemsToFetch
        self.endInsertRows()

    def headerData(self, index, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if index == 0:
                    return _('#')
                columns = self.get_headers()
                return columns[index - 1]
            if orientation == Qt.Vertical:
                return str(index+1)

    def data(self, index, role=None):
        if role == Qt.DisplayRole:
            try:
                row = index.row()
                column = index.column()
                if column == 0:
                    answer = row + 1
                else:
                    obj = self.cache[index.row()]
                    answer = obj.cached_values[index.column() - 1]
                return answer
            except Exception as e:
                logging.exception(str(e))
        return

    def clear_filter(self, remove_condition=True):
        if remove_condition:
            self.filter.clear()
        if self.filter_backup is not None and len(self.filter_backup):
            whole_list = self.get_source_array()
            whole_list.extend(self.filter_backup)
            self.set_source_array(whole_list)
            self.filter_backup.clear()

    def set_filter_for_column(self, column_num, filter_regexp):
        self.filter.update({column_num: re.escape(filter_regexp)})

    def apply_filter(self):
        # get initial list and filter it
        current_array = self.get_source_array()
        current_array.extend(self.filter_backup)
        self.filter_backup.clear()
        for column in self.filter.keys():
            check_regexp = self.filter.get(column)
            check = re.compile(check_regexp)
            # current_array = list(filter(lambda x:  check.match(self.get_item(x, column)), current_array))
            i = 0
            while i < len(current_array):
                value = self.get_item(current_array[i], column)
                if not check.match(value):
                    self.filter_backup.append(current_array.pop(i))
                    i -= 1
                i += 1

        # set main list to result
        # note, unfiltered items are in filter_backup
        self.set_source_array(current_array)

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
            obj = self.cache[cur_pos].cached_values
            for column in columns:
                value = str(obj[column])
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
            obj = self.cache[cur_pos].cached_values
            for column in columns:
                value = str(obj[column])
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
            obj = self.cache[cur_pos].cached_values
            for column in columns:
                value = str(obj[column])
                if check.search(value):
                    self.search_offset = cur_pos
                    self.search_old = self.search
                    return
            i += 1

        self.search_offset = -1

    def sort(self, p_int, order=None):
        """Sort table by given column number.
        """

        if p_int > 0:  # process vertical header
            p_int -= 1

        def sort_key(x):
            item = self.get_item(x, p_int)
            return item is None, str(type(item)), item
        try:
            self.layoutAboutToBeChanged.emit()

            source_array = self.get_source_array()

            if len(source_array):
                source_array = sorted(source_array, key=sort_key, reverse=(order == Qt.DescendingOrder))
                self.set_source_array(source_array)

            self.layoutChanged.emit()
        except Exception as e:
            logging.error(str(e))

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)

    def get_item(self, obj, n_col):
        # return self.get_values_from_object(obj)[n_col]
        return obj.cached_values[n_col]


class PersonMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.init_cache()

    def get_headers(self):
        return [_('Last name'), _('First name'), _('Sex'), _('Qualification title'), _('Group'), _('Team'),
                _('Year title'), _('Bib'), _('Start'), _('Start group'), _('Card title'), _('Rented card'),
                _('Comment'), _('World code title'), _('National code title'), _('Out of competition title'),
                _('Result count title')]

    def init_cache(self):
        self.cache = self.race.persons

    def duplicate(self, position):
        person = self.race.persons[position]
        new_person = copy(person)
        new_person.id = uuid.uuid4()
        new_person.bib = 0
        new_person.card_number = 0
        self.race.persons.insert(position, new_person)

    def set_source_array(self, array):
        self.race.persons = array
        self.init_cache()


class ResultMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.values = None
        self.count = None
        self.init_cache()

    def get_headers(self):
        return [_('Last name'), _('First name'), _('Group'), _('Team'), _('Bib'), _('Card title'),
                _('Start'), _('Finish'), _('Result'), _('Status'), _('Credit'), _('Penalty'), _('Penalty legs title'),
                _('Place'), _('Type'), _('Rented card')]

    def init_cache(self):
        self.cache = self.race.results

    def set_source_array(self, array):
        self.race.results = array
        self.init_cache()

    def duplicate(self, position):
        result = self.race.results[position]
        new_result = copy(result)
        new_result.id = uuid.uuid4()
        new_result.splits = deepcopy(result.splits)
        self.race.results.insert(position, new_result)

    def set_source_array(self, array):
        self.race.results = array
        self.init_cache()


class GroupMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.init_cache()

    def get_headers(self):
        return [_('Name'), _('Full name'), _('Course name'), _('Start fee title'), _('Type'), _('Length title'),
                _('Point count title'), _('Climb title'), _('Sex'), _('Min year title'),
                _('Max year title'), _('Start interval title'), _('Start corridor title'),
                _('Order in corridor title')]

    def init_cache(self):
        self.cache = self.race.groups

    def set_source_array(self, array):
        self.race.groups = array
        self.init_cache()


class CourseMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.init_cache()

    def get_headers(self):
        return [_('Name'), _('Length title'), _('Point count title'), _('Climb title'), _('Controls')]

    def init_cache(self):
        self.cache=self.race.courses

    def duplicate(self, position):
        course = self.race.courses[position]
        new_course = copy(course)
        new_course.id = uuid.uuid4()
        new_course.name = new_course.name + '_'
        new_course.controls = deepcopy(course.controls)
        self.race.courses.insert(position, new_course)

    def set_source_array(self, array):
        self.race.courses = array
        self.init_cache()


class OrganizationMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.init_cache()

    def get_headers(self):
        return [_('Name'), _('Code'), _('Country'), _('Region'), _('Contact')]

    def init_cache(self):
        self.cache = self.race.organizations

    def duplicate(self, position):
        organization = self.race.organizations[position]
        new_organization = copy(organization)
        new_organization.id = uuid.uuid4()
        new_organization.name = new_organization.name + '_'
        self.race.organizations.insert(position, new_organization)

    def set_source_array(self, array):
        self.race.organizations = array
        self.init_cache()
