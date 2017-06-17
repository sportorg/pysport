import sys
import traceback

from PyQt5 import QtCore
from PyQt5.QtCore import QSortFilterProxyModel, QModelIndex, QTime, QDateTime
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QLineEdit, QComboBox, QCompleter, QSpinBox, QApplication, QTimeEdit, QTextEdit, QCheckBox, QTableView, QDialog, \
    QPushButton
from datetime import date, datetime

from sportorg.app.models.memory import race, Person, find
from sportorg.app.models.model import Group, Organization, Participation, ControlCard


def get_groups():
    gr = Group
    ret = list()
    try:
        for i in race().groups:
            ret.append(i.name)
        return ret
    except:
        return ['', 'M12', 'M14', 'M16', 'M21', 'D12', 'D14', 'M16', 'D21']

def get_teams():
    ret = list()
    ret.append('')
    try:
        for i in race().organizations:
            ret.append(i.name)
        return ret
    except:
        return ['', 'Тюменская обл.', 'Курганская обл.', 'Челябинская обл.', 'Республика Коми', 'г.Москва',
                'ХМАО-Югра']

#Deprecated
def get_teams_db():
    team = Organization
    ret = list()
    try:
        for i in team.select():
            ret.append(i.name)
        return ret
    except:
        return ['', 'Тюменская обл.', 'Курганская обл.', 'Челябинская обл.', 'Республика Коми', 'г.Москва', 'ХМАО-Югра']


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


class AdvComboBox(QComboBox):
    """
    Combo with autocomplete
    Found in Internet by Sergei
    """

    def __init__(self, parent=None):
        super(AdvComboBox, self).__init__(parent)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)

        # add a filter model to filter matching items
        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        # add a completer, which uses the filter model
        self.completer = QCompleter(self.pFilterModel, self)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)

        self.setCompleter(self.completer)

        # connect signals

        def filter_function(text):
            self.pFilterModel.setFilterFixedString(str(text))

        self.lineEdit().textEdited.connect(filter_function)
        self.completer.activated.connect(self.on_completer_activated)

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        if text:
            index = self.findText(str(text))
            self.setCurrentIndex(index)


class EntryEditDialog(QDialog):
    def __init__(self, table=None, index=None):
        super().__init__()
        self.init_ui()
        if table is not None:
            self.set_values_from_table(table, index)

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle('Entry properties')
        self.setWindowIcon(QIcon('sportorg.ico'))
        self.setGeometry(100, 100, 350, 500)
        self.setToolTip('Main Window')

        self.layout = QFormLayout(self)
        self.label_surname = QLabel('Last name')
        self.item_surname = QLineEdit()
        self.layout.addRow(self.label_surname, self.item_surname)

        self.label_name = QLabel('Name')
        self.item_name = AdvComboBox()
        self.item_name.addItems(get_names())
        self.layout.addRow(self.label_name, self.item_name)

        self.label_group = QLabel('Group')
        self.item_group = AdvComboBox()
        self.item_group.addItems(get_groups())
        self.layout.addRow(self.label_group, self.item_group)

        self.label_team = QLabel('Team')
        self.item_team = AdvComboBox()
        self.item_team.addItems(get_teams())
        self.layout.addRow(self.label_team, self.item_team)

        self.label_year = QLabel('Year of birth')
        self.item_year = QSpinBox()
        self.item_year.setMinimum(0)
        self.item_year.setMaximum(date.today().year)
        self.item_year.editingFinished.connect(self.year_change)
        self.layout.addRow(self.label_year, self.item_year)

        self.label_qual = QLabel('Qualification')
        self.item_qual = AdvComboBox()
        self.item_qual.addItems(['б/р', '1ю', '2ю', '3ю', '1', '2', '3', 'КМС', 'МС', 'МСМК', 'ЗМС'])
        self.layout.addRow(self.label_qual, self.item_qual)

        self.label_bib = QLabel('Bib')
        self.item_bib = QSpinBox()
        self.item_bib.setMinimum(0)
        self.item_bib.setMaximum(100000)
        self.layout.addRow(self.label_bib, self.item_bib)

        self.label_start = QLabel('Start time')
        self.item_start = QTimeEdit()
        self.item_start.setDisplayFormat('hh:mm:ss')
        self.layout.addRow(self.label_start, self.item_start)

        self.label_card = QLabel('Punch card #')
        self.item_card = QSpinBox()
        self.item_card.setMinimum(0)
        self.item_card.setMaximum(9999999)
        self.layout.addRow(self.label_card, self.item_card)

        self.item_rented = QCheckBox('rented card')
        self.item_paid = QCheckBox('is paid')
        self.item_classified = QCheckBox('is classified')
        self.item_personal = QCheckBox('personal participation')
        self.layout.addRow(self.item_rented, self.item_paid)
        self.layout.addRow(self.item_classified, self.item_personal)

        self.label_comment = QLabel('Comment')
        self.item_comment = QTextEdit()
        self.layout.addRow(self.label_comment, self.item_comment)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except:
                print(sys.exc_info())
                traceback.print_exc()
            self.close()

        self.button_ok = QPushButton('OK')
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton('Cancel')
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

    def set_values_from_table(self, table, index):
        self.table = table
        self.current_index = index
        assert (isinstance(table, QTableView))
        model = table.model()
        assert (isinstance(model, QSortFilterProxyModel))
        orig_index = model.mapToSource(index)
        assert (isinstance(orig_index, QModelIndex))
        orig_index_int = orig_index.row()

        current_object = race().persons[orig_index_int]
        assert (isinstance(current_object, Person))
        self.current_object = current_object
        self.item_surname.setText(current_object.surname)
        self.item_name.setCurrentText(current_object.name)
        if current_object.group is not None:
            self.item_group.setCurrentText(current_object.group.name)
        if current_object.organization is not None:
            self.item_team.setCurrentText(current_object.organization.name)
        if current_object.year is not None:
            self.item_year.setValue(int(current_object.year))
        if current_object.qual is not None:
            self.item_qual.setCurrentText(str(current_object.qual))
        if current_object.bib is not None:
            self.item_bib.setValue(int(current_object.bib))
        if current_object.result is not None:

            t = current_object.result.start_time
            if t is not None:
                assert(isinstance(t, datetime))
                time = QTime()
                time.setHMS(t.hour, t.minute, t.second, t.microsecond)
                self.item_start.setTime(time)

        if current_object.card_number is not None:
            self.item_card.setValue(int(current_object.card_number))

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
        if person.group.name != self.item_group.currentText():
            person.group = find(race().groups, name=self.item_group.currentText())
            changed = True
        if person.organization.name != self.item_team.currentText():
            person.organization = find(race().organizations, name=self.item_team.currentText())
            changed = True
        if person.year != str(self.item_year.value()):
            person.year = str(self.item_year.value())
            changed = True
        if person.qual != self.item_qual.currentText():
            person.qual = self.item_qual.currentText()
            changed = True
        if person.bib != self.item_bib.text() and self.item_bib.text() != '0':
            person.bib = self.item_bib.text()
            changed = True

        t = self.item_start.time()
        now = datetime.now()
        assert(isinstance(t, QTime))
        new_time = datetime(now.year, now.month, now.day, t.hour(), t.minute(), t.second(), t.msec())
        if person.result.start_time != new_time:
            person.result.start_time = new_time
            changed = True

        if (person.card_number is None or person.card_number != self.item_card.text()) \
                and self.item_card.text() != '0':
            person.card_number = self.item_card.text()
            changed = True

        if changed:
            table = self.table
            #table.model().sourceModel().update_one_object(part, table.model().mapToSource(self.current_index).row())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EntryEditDialog()
    sys.exit(app.exec_())
