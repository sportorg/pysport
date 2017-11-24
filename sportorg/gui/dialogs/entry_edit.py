import logging
import sys
from datetime import date

from PyQt5.QtCore import QModelIndex
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QLineEdit, QSpinBox, QApplication, QTimeEdit, QTextEdit, QCheckBox, QDialog, \
    QPushButton
from sportorg.models.memory import race, Person, find, Qualification, Limit

from sportorg import config
from sportorg.modules.utils.custom_controls import AdvComboBox
from sportorg.modules.utils.utils import time_to_qtime, time_to_otime
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.result.result_calculation import ResultCalculation


def get_groups():
    ret = []
    try:
        for i in race().groups:
            ret.append(i.name)
        return ret
    except Exception as e:
        logging.exception(str(e))
        return ['', 'M12', 'M14', 'M16', 'M21', 'D12', 'D14', 'M16', 'D21']


def get_teams():
    ret = ['']
    try:
        for i in race().organizations:
            ret.append(i.name)
        return ret
    except Exception as e:
        logging.exception(str(e))
        return ['', 'Тюменская обл.', 'Курганская обл.', 'Челябинская обл.', 'Республика Коми', 'г.Москва',
                'ХМАО-Югра']


def get_names():
    names = [
        '',
        'Адик',
        'Азамат',
        'Александр',
        'Александра',
        'Алексей',
        'Алена',
        'Алина',
        'Альберт',
        'Анастасия',
        'Андрей',
        'Анна',
        'Антон',
        'Арина',
        'Аркадий',
        'Артем',
        'Артём',
        'Артур',
        'Боймат',
        'Вадим',
        'Валентина',
        'Валерий',
        'Валерия',
        'Варвара',
        'Василий',
        'Василина',
        'Вениамин',
        'Вера',
        'Вероника',
        'Виктор',
        'Виктория',
        'Виталий',
        'Влада',
        'Владимир',
        'Владислав',
        'Всеволод',
        'Вячеслав',
        'Галина',
        'Георгий',
        'Григорий',
        'Даниил',
        'Данил',
        'Данила',
        'Данис',
        'Дания',
        'Дарья',
        'Денис',
        'Диана',
        'Дмитрий',
        'Евангелина',
        'Евгений',
        'Евгения',
        'Егор',
        'Екатерина',
        'Елена',
        'Елизавета',
        'Заур',
        'Иван',
        'Игорь',
        'Илья',
        'Ирина',
        'Карина',
        'Кирилл',
        'Константин',
        'Кристина',
        'Ксения',
        'Лариса',
        'Лев',
        'Леонид',
        'Лидия',
        'Любовь',
        'Людмила',
        'Макар',
        'Максим',
        'Маргарита',
        'Марина',
        'Мария',
        'Матвей',
        'Михаил',
        'Надежда',
        'Наталья',
        'Никит',
        'Никита',
        'Николай',
        'Нина',
        'Оксана',
        'Олег',
        'Олеся',
        'Ольга',
        'Павел',
        'Полина',
        'Равиль',
        'Раиса',
        'Рамзия',
        'Роман',
        'Руслан',
        'Савелий',
        'Светлана',
        'Святослав',
        'Семён',
        'Сергей',
        'Софья',
        'Станислав',
        'Степан',
        'Тамара',
        'Татьяна',
        'Тимофей',
        'Тимур',
        'Ульяна',
        'Филипп',
        'Шойра',
        'Эльза',
        'Юлия',
        'Юрий',
        'Ярослав',
        'Ярослава'
    ]
    return names


class EntryEditDialog(QDialog):
    def __init__(self, table=None, index=None):
        super().__init__()
        self.is_ok = {}
        self.init_ui()
        if table is not None:
            self.set_values_from_table(table, index)

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle(_('Entry properties'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)
        self.label_surname = QLabel(_('Last name'))
        self.item_surname = QLineEdit()
        self.layout.addRow(self.label_surname, self.item_surname)

        self.label_name = QLabel(_('First name'))
        self.item_name = AdvComboBox()
        self.item_name.addItems(get_names())
        self.layout.addRow(self.label_name, self.item_name)

        self.label_group = QLabel(_('Group'))
        self.item_group = AdvComboBox()
        self.item_group.addItems(get_groups())
        self.layout.addRow(self.label_group, self.item_group)

        self.label_team = QLabel(_('Team'))
        self.item_team = AdvComboBox()
        self.item_team.addItems(get_teams())
        self.layout.addRow(self.label_team, self.item_team)

        self.label_year = QLabel(_('Year of birth'))
        self.item_year = QSpinBox()
        self.item_year.setMinimum(0)
        self.item_year.setMaximum(date.today().year)
        self.item_year.editingFinished.connect(self.year_change)
        self.layout.addRow(self.label_year, self.item_year)

        self.label_qual = QLabel(_('Qualification'))
        self.item_qual = AdvComboBox()
        for i in list(Qualification):
            self.item_qual.addItem(i.get_title())
        self.layout.addRow(self.label_qual, self.item_qual)

        self.is_ok['bib'] = True
        self.label_bib = QLabel(_('Bib'))
        self.item_bib = QSpinBox()
        self.item_bib.setMinimum(0)
        self.item_bib.setMaximum(Limit.BIB)
        self.item_bib.valueChanged.connect(self.check_bib)
        self.layout.addRow(self.label_bib, self.item_bib)

        self.label_bib_info = QLabel('')
        self.layout.addRow(QLabel(''), self.label_bib_info)

        self.label_start = QLabel(_('Start time'))
        self.item_start = QTimeEdit()
        self.item_start.setDisplayFormat('hh:mm:ss')
        self.layout.addRow(self.label_start, self.item_start)

        self.label_start_group = QLabel(_('Start group'))
        self.item_start_group = QSpinBox()
        self.item_start_group.setMinimum(0)
        self.item_start_group.setMaximum(99)
        self.layout.addRow(self.label_start_group, self.item_start_group)

        self.is_ok['card'] = True
        self.label_card = QLabel(_('Punch card #'))
        self.item_card = QSpinBox()
        self.item_card.setMinimum(0)
        self.item_card.setMaximum(9999999)
        self.item_card.valueChanged.connect(self.check_card)
        self.layout.addRow(self.label_card, self.item_card)

        self.label_card_info = QLabel('')
        self.layout.addRow(QLabel(''), self.label_card_info)

        self.item_rented = QCheckBox(_('rented card'))
        self.item_paid = QCheckBox(_('is paid'))
        self.item_out_of_competition = QCheckBox(_('out of competition'))
        self.item_personal = QCheckBox(_('personal participation'))
        self.layout.addRow(self.item_rented, self.item_out_of_competition)
        self.layout.addRow(self.item_paid, self.item_personal)

        self.label_comment = QLabel(_('Comment'))
        self.item_comment = QTextEdit()
        self.layout.addRow(self.label_comment, self.item_comment)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(str(e))
            self.close()

        self.button_ok = QPushButton(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

        self.show()

    def year_change(self):
        """
        Convert 2 digits of year to 4
        2 -> 2002
        11 - > 2011
        33 -> 1933
        56 -> 1956
        98 - > 1998
        0 -> 0 exception!
        """
        widget = self.sender()
        assert isinstance(widget, QSpinBox)
        year = int(widget.value())
        if 0 < year < 100:
            cur_year = date.today().year
            new_year = cur_year - cur_year % 100 + year
            if new_year > cur_year:
                new_year -= 100
            widget.setValue(new_year)

    def items_ok(self):
        ret = True
        for item_name in self.is_ok.keys():
            if self.is_ok[item_name] is not True:
                ret = False
                break
        return ret

    def check_bib(self):
        bib = self.item_bib.value()
        self.label_bib_info.setText('')
        if bib:
            person = find(race().persons, bib=bib)
            if person:
                if person.bib == self.current_object.bib:
                    self.button_ok.setEnabled(True)
                    return
                self.button_ok.setDisabled(True)
                self.is_ok['bib'] = False
                info = '{}\n{}'.format(_('Number already exists'), person.full_name)
                if person.group:
                    info = '{}\n{}: {}'.format(info, _('Group'), person.group.name)
                self.label_bib_info.setText(info)
            else:
                self.label_bib_info.setText(_('Number is unique'))
                self.is_ok['bib'] = True
                if self.items_ok():
                    self.button_ok.setEnabled(True)
        else:
            self.button_ok.setEnabled(True)

    def check_card(self):
        number = self.item_card.value()
        self.label_card_info.setText('')
        if number:
            person = None
            for _p in race().persons:
                if _p.sportident_card is not None and int(_p.sportident_card) == number:
                    person = _p
                    break
            if person:
                if person.sportident_card == self.current_object.sportident_card:
                    self.button_ok.setEnabled(True)
                    return
                self.button_ok.setDisabled(True)
                self.is_ok['card'] = False
                info = '{}\n{}'.format(_('Card number already exists'), person.full_name)
                if person.group:
                    info = '{}\n{}: {}'.format(info, _('Group'), person.group.name)
                if person.bib:
                    info = '{}\n{}: {}'.format(info, _('Bib'), person.bib)
                self.label_card_info.setText(info)
            else:
                self.label_card_info.setText(_('Card number is unique'))
                self.is_ok['card'] = True
                if self.items_ok():
                    self.button_ok.setEnabled(True)
        else:
            self.button_ok.setEnabled(True)

    def set_values_from_table(self, table, index):
        self.table = table
        self.current_index = index

        assert (isinstance(index, QModelIndex))
        orig_index_int = index.row()

        current_object = race().persons[orig_index_int]
        assert (isinstance(current_object, Person))
        self.current_object = current_object
        self.item_surname.setText(current_object.surname)
        self.item_name.setCurrentText(current_object.name)
        if current_object.group is not None:
            self.item_group.setCurrentText(current_object.group.name)
        if current_object.organization is not None:
            self.item_team.setCurrentText(current_object.organization.name)
        if current_object.year:
            self.item_year.setValue(int(current_object.year))
        if current_object.qual:
            self.item_qual.setCurrentText(current_object.qual.get_title())
        if current_object.bib:
            self.item_bib.setValue(int(current_object.bib))
        if current_object.start_time is not None:
            time = time_to_qtime(current_object.start_time)
            self.item_start.setTime(time)
        if current_object.start_group is not None:
            self.item_start_group.setValue(int(current_object.start_group))

        if current_object.sportident_card is not None:
            self.item_card.setValue(int(current_object.sportident_card))

        self.item_out_of_competition.setChecked(current_object.is_out_of_competition)

        self.item_comment.setText(current_object.comment)

    def apply_changes_impl(self):
        changed = False
        person = self.current_object
        assert (isinstance(person, Person))
        if person.name != self.item_name.currentText():
            person.name = self.item_name.currentText()
            changed = True
        if person.surname != self.item_surname.text():
            person.surname = self.item_surname.text()
            changed = True
        if (person.group is not None and person.group.name != self.item_group.currentText()) or\
                (person.group is None and len(self.item_group.currentText()) > 0):
            person.group = find(race().groups, name=self.item_group.currentText())
            # if person.result:
            #     logging.info('Old status {}'.format(person.result.status))
            #     ResultChecker.checking(person.result)
            #     logging.info('New status {}'.format(person.result.status))
            changed = True
        if (person.organization is not None and person.organization.name != self.item_team.currentText()) or \
                (person.organization is None and len(self.item_team.currentText()) > 0):
            person.organization = find(race().organizations, name=self.item_team.currentText())
            changed = True
        if person.year != self.item_year.value():
            person.year = self.item_year.value()
            changed = True
        if person.qual.get_title() != self.item_qual.currentText():
            person.qual = Qualification.get_qual_by_name(self.item_qual.currentText())
            changed = True
        if person.bib != self.item_bib.value() and self.item_bib.value():
            person.bib = self.item_bib.value()
            changed = True

        new_time = time_to_otime(self.item_start.time())
        if person.start_time != new_time:
            person.start_time = new_time
            changed = True

        if person.start_group != self.item_start_group.value() and self.item_start_group.value():
            person.start_group = self.item_start_group.value()
            changed = True

        if (person.sportident_card is None or int(person.sportident_card) != self.item_card.value()) \
                and self.item_card.value:
            person.sportident_card = race().new_sportident_card(self.item_card.value())
            changed = True

        if person.is_out_of_competition != self.item_out_of_competition.isChecked():
            person.is_out_of_competition = self.item_out_of_competition.isChecked()
            changed = True

        if person.comment != self.item_comment.toPlainText():
            person.comment = self.item_comment.toPlainText()
            changed = True

        if changed:
            ResultCalculation().process_results()
            GlobalAccess().get_main_window().refresh()
            # table.model().sourceModel().update_one_object(part, table.model().mapToSource(self.current_index).row())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EntryEditDialog()
    sys.exit(app.exec_())
