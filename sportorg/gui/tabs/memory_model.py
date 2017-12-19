import logging
import re
from abc import abstractmethod

from PyQt5.QtCore import QVariant, QAbstractTableModel, Qt, QSortFilterProxyModel
from typing import List

from sportorg.language import _
from sportorg.models.memory import race, Result, Group, Course, Organization, SystemType
from sportorg.utils.time import time_to_hhmmss


class AbstractSportOrgMemoryModel(QAbstractTableModel):
    """
    Used to specify common table behavior
    """
    def __init__(self):
        super().__init__()
        self.cache = []
        self.init_cache()
        self.filter = {}

        # temporary list, used to keep records, that are not filtered
        # main list will have only filtered elements
        # while clearing of filter list is recovered from backup
        self.filter_backup = []

        self.search = ''
        self.search_backup = []

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

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.get_headers())

    def rowCount(self, parent=None, *args, **kwargs):
        ret = len(self.cache)
        return ret

    def headerData(self, index, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                columns = self.get_headers()
                return _(columns[index])
            if orientation == Qt.Vertical:
                return str(index+1)

    def data(self, index, role=None):
        if role == Qt.DisplayRole:
            # start = time.time()
            # answer = str(index.row()) + ' ' + str(index.column())
            answer = ''
            try:
                # answer = self.get_participation_data(index.row())[index.column()]
                row = index.row()
                column = index.column()
                answer = self.cache[row][column]
            except Exception as e:
                logging.exception(str(e))

            # end = time.time()
            # logging.debug('Data() ' + str(index.row()) + ' ' + str(index.column()) + ': ' + str(end - start) + ' s')
            return QVariant(answer)

        return QVariant()

    def clear_filter(self, remove_condition=True):
        if remove_condition:
            self.filter.clear()
        if self.filter_backup is not None and len(self.filter_backup):
            whole_list = self.get_source_array()
            whole_list.extend(self.filter_backup)
            self.set_source_array(whole_list)
            self.filter_backup = []

    def set_filter_for_column(self, column_num, filter_regexp):
        self.filter.update({column_num: filter_regexp})

    def apply_filter(self):
        # get initial list and filter it
        current_array = self.get_source_array()
        current_array.extend(self.filter_backup)

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
        self.init_cache()

    def clear_search(self, remove_condition=True):
        if remove_condition:
            self.search = ''
        if self.search_backup is not None and len(self.search_backup):
            whole_list = self.get_source_array()
            whole_list.extend(self.search_backup)
            self.set_source_array(whole_list)
            self.search_backup = []

    def apply_search(self):
        current_array = self.get_source_array()
        current_array.extend(self.search_backup)
        check_regexp = self.search
        check = re.compile(check_regexp)

        count_columns = len(self.get_headers())
        columns = range(count_columns)
        i = 0
        while i < len(current_array):
            obj = self.get_values_from_object(current_array[i])
            for column in columns:
                value = str(obj[column])
                if check.match(value):
                    i += 1
                    break
            else:
                self.search_backup.append(current_array.pop(i))

        self.set_source_array(current_array)
        self.init_cache()

    def sort(self, p_int, order=None):
        """Sort table by given column number.
        """
        try:
            self.layoutAboutToBeChanged.emit()

            source_array = self.get_source_array()

            if len(source_array):
                source_array = sorted(source_array,
                                      key=lambda x: (self.get_item(x, p_int) is None,
                                                     str(type(self.get_item(x, p_int))),
                                                     self.get_item(x, p_int)))
                if order == Qt.DescendingOrder:
                    source_array = source_array[::-1]

                self.set_source_array(source_array)

                self.init_cache()
            self.layoutChanged.emit()
        except Exception as e:
            logging.exception(str(e))

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)

    def get_item(self, obj, n_col):
        return self.get_values_from_object(obj)[n_col]


class PersonMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.init_cache()

    def get_headers(self):
        return ['Last name', 'First name', 'Sex', 'Qualification', 'Group', 'Team', 'Year', 'Bib', 'Start',
                'Start group', 'Card', 'Rented card', 'Comment', 'World code', 'National code', 'Out of competition']

    def init_cache(self):
        self.cache.clear()
        for i in range(len(race().persons)):
            self.cache.append(self.get_participation_data(i))

    def get_participation_data(self, position):
        return self.get_values_from_object(race().persons[position])

    def get_values_from_object(self, obj):
        ret = []
        person = obj

        ret.append(person.surname)
        ret.append(person.name)
        ret.append(person.sex.get_title())
        if person.qual:
            ret.append(person.qual.get_title())
        else:
            ret.append('')
        if person.group:
            ret.append(person.group.name)
        else:
            ret.append('')
        if person.organization:
            ret.append(person.organization.name)
        else:
            ret.append('')
        ret.append(str(person.year))
        ret.append(str(person.bib))
        if person.start_time:
            ret.append(time_to_hhmmss(person.start_time))
        else:
            ret.append('')
        ret.append(str(person.start_group))
        ret.append(str(person.sportident_card) if person.sportident_card is not None else '')
        ret.append(_('rented stub'))
        ret.append(person.comment)
        ret.append(str(person.world_code) if person.world_code else '')
        ret.append(str(person.national_code) if person.national_code else '')

        out_of_comp_status = ''
        if person.is_out_of_competition:
            out_of_comp_status = _('o/c')
        ret.append(out_of_comp_status)

        return ret

    def get_source_array(self):
        return race().persons

    def set_source_array(self, array):
        race().persons = array


class ResultMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.values = None
        self.count = None

    def get_headers(self):
        return ['Last name', 'First name', 'Group', 'Team', 'Bib', 'Card', 'Start', 'Finish', 'Result',
                'Status', 'Penalty', 'Place', 'Type']

    def init_cache(self):
        self.cache.clear()
        for i in range(len(race().results)):
            self.cache.append(self.get_participation_data(i))

    def get_participation_data(self, position):
        ret = self.get_values_from_object(race().results[position])
        return ret

    def get_values_from_object(self, result):
        i = result
        assert (isinstance(i, Result))
        person = i.person
        group = ''
        team = ''
        first_name = ''
        last_name = ''
        bib = 0
        sportident_card = ''
        if i.system_type == SystemType.SPORTIDENT:
            sportident_card = str(result.sportident_card) if result.sportident_card is not None else ''
        if person:
            first_name = person.name
            last_name = person.surname
            bib = person.bib

            if person.group:
                group = person.group.name

            if person.organization:
                team = person.organization.name

        start = ''
        if i.start_time:
            start = str(i.start_time)

        finish = ''
        if i.finish_time:
            finish = str(i.finish_time)

        return [
            last_name,
            first_name,
            group,
            team,
            str(bib),
            sportident_card,
            start,
            finish,
            i.get_result(),
            i.status.get_title(),
            time_to_hhmmss(i.get_penalty_time()),
            str(i.place) if i.place is not None else '',
            str(i.system_type)
        ]

    def get_source_array(self):
        return race().results

    def set_source_array(self, array):
        race().results = array


class GroupMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()

    def get_headers(self):
        return ['Name', 'Full name', 'Course name', 'Course type', 'Length', 'Point count', 'Climb', 'Sex', 'Min age',
                'Max age', 'Start interval', 'Start corridor', 'Order in corridor']

    def init_cache(self):
        self.cache.clear()
        for i in range(len(race().groups)):
            self.cache.append(self.get_data(i))

    def get_data(self, position):
        ret = self.get_values_from_object(race().groups[position])
        return ret

    def get_values_from_object(self, group):
        assert (isinstance(group, Group))
        course = group.course
        if course is None:
            course = Course()

        control_count = 0
        if course.controls is not None:
            control_count = len(course.controls)

        return [
            group.name,
            group.long_name,
            course.name,
            course.type,
            str(course.length),
            str(control_count),
            str(course.climb),
            group.sex.get_title(),
            str(group.min_age),
            str(group.max_age),
            str(group.start_interval),
            str(group.start_corridor),
            str(group.order_in_corridor),
        ]

    def get_source_array(self):
        return race().groups

    def set_source_array(self, array):
        race().groups = array


class CourseMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()

    def get_headers(self):
        return ['Name', 'Course type', 'Length', 'Point count', 'Climb', 'Controls']

    def init_cache(self):
        self.cache.clear()
        for i in range(len(race().courses)):
            self.cache.append(self.get_data(i))

    def get_data(self, position):
        ret = self.get_values_from_object(race().courses[position])
        return ret

    def get_values_from_object(self, course):
        assert (isinstance(course, Course))
        if course is None:
            course = Course()

        return [
            course.name,
            course.type,
            str(course.length),
            str(len(course.controls)),
            str(course.climb),
            ' '.join(course.get_code_list()),
        ]

    def get_source_array(self):
        return race().courses

    def set_source_array(self, array):
        race().courses = array


class TeamMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()

    def get_headers(self):
        return ['Name', 'Address', 'Country', 'Region', 'City', 'Contact']

    def init_cache(self):
        self.cache.clear()
        for i in range(len(race().organizations)):
            self.cache.append(self.get_data(i))

    def get_data(self, position):
        ret = self.get_values_from_object(race().organizations[position])
        return ret

    def get_values_from_object(self, team):
        assert (isinstance(team, Organization))
        if team is None:
            team = Organization()

        return [
            team.name,
            team.address.street,
            team.country.name,
            team.region,
            team.city,
            team.contact.value
        ]

    def get_source_array(self):
        return race().organizations

    def set_source_array(self, array):
        race().organizations = array


class PersonProxyModel(QSortFilterProxyModel):

    def __init__(self, parent):
        super(PersonProxyModel, self).__init__(parent)
        self.filter_map = None
        self.filter_applied = False

    def clear_filter(self):
        self.filter_map = []
        for i in range(self.sourceModel().columnCount()):
            self.filter_map.append('')
        self.filter_applied = False

    def set_filter_for_column(self, column, filter_string):
        if self.filter_map is None:
            self.clear_filter()
        self.filter_map[column] = filter_string
        self.invalidateFilter()
        self.filter_applied = True

    def filterAcceptsRow(self, row, index):
        if not self.filter_applied:
            return True
        try:
            source_model = self.sourceModel()
            size = source_model.columnCount()
            for i in range(size):
                if self.filter_map is not None and self.filter_map[i] is not None and self.filter_map[i] != '':
                    filter_string = self.filter_map[i]
                    cell = source_model.data(source_model.index(row, i), Qt.DisplayRole)
                    if str(cell.value()).find(filter_string) == -1:
                        return False
        except Exception as e:
            logging.exception(str(e))
        return True
