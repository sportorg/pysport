import re

from sportorg.app.modules.utils.utils import time_to_hhmmss
from sportorg.language import _
import logging

from PyQt5.QtCore import QVariant, QAbstractTableModel, Qt, QSortFilterProxyModel

from sportorg.app.models.memory import race, Result, Group, Course, Organization


class AbstractSportOrgMemoryModel (QAbstractTableModel):
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

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.get_headers())

    def rowCount(self, parent=None, *args, **kwargs):
        ret = len(self.cache)
        return ret

    def get_headers(self):
        pass

    def headerData(self, index, orientation, role=None):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            columns = self.get_headers()
            return _(columns[index])

    def init_cache(self):
        pass

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
                logging.exception(e)

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

    def sort(self, Ncol, order):
        """Sort table by given column number.
        """
        try:
            self.layoutAboutToBeChanged.emit()

            source_array = self.get_source_array()

            if len(source_array):
                source_array = sorted(source_array,
                                      key=lambda x: (self.get_item(x, Ncol) is None,
                                                     str(type(self.get_item(x, Ncol))),
                                                     self.get_item(x, Ncol)))
                if order == Qt.DescendingOrder:
                    source_array = source_array[::-1]

                self.set_source_array(source_array)

                self.init_cache()
            self.layoutChanged.emit()
        except Exception as e:
            logging.exception(str(e))

    def get_values_from_object(self, obj):
        pass

    def get_item(self, obj, n_col):
        return self.get_values_from_object(obj)[n_col]

    def get_source_array(self):
        pass

    def set_source_array(self, array):
        pass


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
        ret.append(person.sex)
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
        ret.append(person.year)
        ret.append(person.bib)
        if person.start_time:
            ret.append(time_to_hhmmss(person.start_time))
        else:
            ret.append('')
        ret.append(person.start_group)
        ret.append(person.card_number)
        ret.append('rented stub')
        ret.append(person.comment)
        ret.append(person.world_code)
        ret.append(person.national_code)

        out_of_comp_status = ''
        if person.is_out_of_competition:
            out_of_comp_status = _('o/c')
        ret.append(out_of_comp_status)

        return ret

    def get_source_array(self):
        return race().persons

    def set_source_array(self, array):
        race().persons = array

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)


class ResultMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.values = None
        self.count = None

    def get_headers(self):
        return ['Last name', 'First name', 'Group', 'Team', 'Bib', 'Card', 'Start', 'Finish', 'Result',
                'Status', 'Penalty', 'Place']

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
        card_number = str(result.card_number) if result.card_number else ''
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
            start = i.start_time.strftime('%H:%M:%S')

        finish = ''
        if i.finish_time:
            finish = i.finish_time.strftime('%H:%M:%S')

        return list([
            last_name,
            first_name,
            group,
            team,
            bib,
            card_number,
            start,
            finish,
            i.get_result(),
            i.status,
            i.penalty_time,
            i.place])

    def get_source_array(self):
        return race().results

    def set_source_array(self, array):
        race().results = array

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)


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

        return list([
            group.name,
            group.long_name,
            course.name,
            course.type,
            course.length,
            control_count,
            course.climb,
            group.sex,
            group.min_age,
            group.max_age,
            group.start_interval,
            group.start_corridor,
            group.order_in_corridor,
        ])

    def get_source_array(self):
        return race().groups

    def set_source_array(self, array):
        race().groups = array

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)


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

        return list([
            course.name,
            course.type,
            course.length,
            len(course.controls),
            course.climb,
            ' '.join(course.get_code_list()),
        ])

    def get_source_array(self):
        return race().courses

    def set_source_array(self, array):
        race().courses = array

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)


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

        return list([
            team.name,
            team.address.street,
            team.country.name,
            team.region,
            team.city,
            team.contact.value
        ])

    def get_source_array(self):
        return race().organizations

    def set_source_array(self, array):
        race().organizations = array

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)


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
