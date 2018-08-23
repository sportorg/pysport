import logging
import re
from abc import abstractmethod

from PyQt5.QtCore import QVariant, QAbstractTableModel, Qt
from typing import List

from sportorg.language import _
from sportorg.models.memory import race, Result, Group, Course, Organization
from sportorg.utils.time import time_to_hhmmss


class AbstractSportOrgMemoryModel(QAbstractTableModel):
    """
    Used to specify common table behavior
    """
    def __init__(self):
        super().__init__()
        self.race = race()
        self.cache = []
        self.init_cache()
        self.filter = {}

        # temporary list, used to keep records, that are not filtered
        # main list will have only filtered elements
        # while clearing of filter list is recovered from backup
        self.filter_backup = []

        self.search = ''
        self.search_old = ''
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

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.get_headers())

    def rowCount(self, parent=None, *args, **kwargs):
        ret = len(self.cache)
        return ret

    def headerData(self, index, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                columns = self.get_headers()
                return columns[index]
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
                logging.error(str(e))

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
        self.init_cache()

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
        max = len(current_array)
        while i < max:
            cur_pos = (self.search_offset + i) % max
            obj = self.get_values_from_object(current_array[cur_pos])
            for column in columns:
                value = str(obj[column])
                if value == self.search:
                    self.search_offset = cur_pos
                    self.search_old = self.search
                    return
            i += 1

        # 2 phase - match
        i = 0
        max = len(current_array)
        while i < max:
            cur_pos = (self.search_offset + i) % max
            obj = self.get_values_from_object(current_array[cur_pos])
            for column in columns:
                value = str(obj[column])
                if check.match(value):
                    self.search_offset = cur_pos
                    self.search_old = self.search
                    return
            i += 1

        # 3 phase - search
        i = 0
        max = len(current_array)
        while i < max:
            cur_pos = (self.search_offset + i) % max
            obj = self.get_values_from_object(current_array[cur_pos])
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
            logging.error(str(e))

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)

    def get_item(self, obj, n_col):
        return self.get_values_from_object(obj)[n_col]


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
        ret.append(person.get_year())
        ret.append(person.bib)
        if person.start_time:
            ret.append(time_to_hhmmss(person.start_time))
        else:
            ret.append('')
        ret.append(person.start_group)
        ret.append(person.card_number)
        ret.append(_('Rented card') if person.is_rented_card else _('Rented stub'))
        ret.append(person.comment)
        ret.append(str(person.world_code) if person.world_code else '')
        ret.append(str(person.national_code) if person.national_code else '')

        out_of_comp_status = ''
        if person.is_out_of_competition:
            out_of_comp_status = _('o/c')
        ret.append(out_of_comp_status)
        ret.append(person.result_count)

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
        return [_('Last name'), _('First name'), _('Group'), _('Team'), _('Bib'), _('Card title'),
                _('Start'), _('Finish'), _('Result'), _('Status'), _('Credit'), _('Penalty'), _('Penalty legs title'),
                _('Place'), _('Type'), _('Rented card')]

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
        bib = result.get_bib()
        rented_card = ''
        if person:
            first_name = person.name
            last_name = person.surname

            if person.group:
                group = person.group.name

            if person.organization:
                team = person.organization.name

            rented_card = _('Rented card') if person.is_rented_card else _('Rented stub')

        start = ''
        if i.get_start_time():
            time_accuracy = race().get_setting('time_accuracy', 0)
            start = i.get_start_time().to_str(time_accuracy)

        finish = ''
        if i.get_finish_time():
            time_accuracy = race().get_setting('time_accuracy', 0)
            finish = i.get_finish_time().to_str(time_accuracy)

        return [
            last_name,
            first_name,
            group,
            team,
            bib,
            i.card_number,
            start,
            finish,
            i.get_result(),
            i.status.get_title(),
            time_to_hhmmss(i.get_credit_time()),
            time_to_hhmmss(i.get_penalty_time()),
            i.penalty_laps,
            i.get_place(),
            str(i.system_type),
            rented_card
        ]

    def get_source_array(self):
        return race().results

    def set_source_array(self, array):
        race().results = array


class GroupMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()

    def get_headers(self):
        return [_('Name'), _('Full name'), _('Course name'), _('Start fee title'), _('Type'), _('Length title'),
                _('Point count title'), _('Climb title'), _('Sex'), _('Min year title'),
                _('Max year title'), _('Start interval title'), _('Start corridor title'),
                _('Order in corridor title')]

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

        control_count = len(course.controls)

        return [
            group.name,
            group.long_name,
            course.name,
            group.price,
            self.race.get_type(group).get_title(),
            course.length,
            control_count,
            course.climb,
            group.sex.get_title(),
            group.min_year,
            group.max_year,
            group.start_interval,
            group.start_corridor,
            group.order_in_corridor,
        ]

    def get_source_array(self):
        return race().groups

    def set_source_array(self, array):
        race().groups = array


class CourseMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()

    def get_headers(self):
        return [_('Name'), _('Length title'), _('Point count title'), _('Climb title'), _('Controls')]

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
            course.length,
            len(course.controls),
            course.climb,
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
        return [_('Name'), _('Address'), _('Country'), _('Region'), _('City'), _('Contact')]

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
            team.address.country.name,
            team.address.state,
            team.address.city,
            team.contact.value
        ]

    def get_source_array(self):
        return race().organizations

    def set_source_array(self, array):
        race().organizations = array
