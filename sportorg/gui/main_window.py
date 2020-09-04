import ast
import logging
import time
from queue import Queue

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import QMainWindow, QMessageBox

from sportorg import config
from sportorg.common.broker import Broker
from sportorg.gui.dialogs.course_edit import CourseEditDialog
from sportorg.gui.dialogs.file_dialog import get_save_file_name
from sportorg.gui.dialogs.group_edit import GroupEditDialog
from sportorg.gui.dialogs.organization_edit import OrganizationEditDialog
from sportorg.gui.dialogs.person_edit import PersonEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.menu import Factory, menu_list
from sportorg.gui.tabs import courses, groups, organizations, persons, results
from sportorg.gui.tabs.memory_model import (
    CourseMemoryModel,
    GroupMemoryModel,
    OrganizationMemoryModel,
    PersonMemoryModel,
    ResultMemoryModel,
)
from sportorg.gui.utils.custom_controls import messageBoxQuestion
from sportorg.language import translate
from sportorg.models.constant import RentCards
from sportorg.models.memory import (
    NotEmptyException,
    Race,
    new_event,
    race,
    set_current_race_index,
)
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.split_calculation import GroupSplits
from sportorg.modules.backup.file import File
from sportorg.modules.configs.configs import Config as Configuration
from sportorg.modules.configs.configs import ConfigFile
from sportorg.modules.live.live import LiveClient
from sportorg.modules.printing.model import (
    NoPrinterSelectedException,
    NoResultToPrintException,
    split_printout,
)
from sportorg.modules.sfr.sfrreader import SFRReaderClient
from sportorg.modules.sound import Sound
from sportorg.modules.sportident.result_generation import ResultSportidentGeneration
from sportorg.modules.sportident.sireader import SIReaderClient
from sportorg.modules.sportiduino.sportiduino import SportiduinoClient
from sportorg.modules.telegram.telegram import TelegramClient


class ConsolePanelHandler(logging.Handler):
    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.setFormatter(logging.Formatter('%(asctime)-15s %(levelname)s %(message)s'))
        self.setLevel('INFO')
        self.parent = parent

    def emit(self, record):
        self.parent.logging(self.format(record))


class MainWindow(QMainWindow):
    def __init__(self, argv=None):
        super().__init__()
        self.menu_factory = Factory(self)
        self.recent_files = []
        self.menu_property = {}
        self.menu_list_for_disabled = []
        self.toolbar_property = {}
        try:
            self.file = argv[1]
            self.add_recent_file(self.file)
        except IndexError:
            self.file = None

        self.log_queue = Queue()
        handler = ConsolePanelHandler(self)
        logging.root.addHandler(handler)
        self.last_update = time.time()
        self.relay_number_assign = False

    def _set_style(self):
        try:
            with open(config.style_dir('default.qss')) as s:
                self.setStyleSheet(s.read())
        except FileNotFoundError:
            pass

    def show_window(self):
        try:
            self.conf_read()
        except Exception as e:
            logging.error(e)
        self._set_style()
        self._setup_ui()
        self._setup_menu()
        self._setup_tab()
        self._setup_statusbar()
        self.show()
        self.post_show()

    def close(self):
        self.conf_write()
        Broker().produce('close')

    def closeEvent(self, _event):
        quit_msg = translate('Save file before exit?')
        reply = messageBoxQuestion(
            self,
            translate('Question'),
            quit_msg,
            QMessageBox.Save | QMessageBox.No | QMessageBox.Cancel,
        )

        if reply == QMessageBox.Save:
            self.save_file()
            self.close()
            _event.accept()
        elif reply == QMessageBox.No:
            self.close()
            _event.accept()
        else:
            _event.ignore()

    def resizeEvent(self, e):
        Broker().produce('resize', self.get_size())

    def conf_read(self):
        Configuration().read()
        if Configuration().parser.has_section(ConfigFile.PATH):
            try:
                recent_files = ast.literal_eval(
                    Configuration().parser.get(
                        ConfigFile.PATH, 'recent_files', fallback='[]'
                    )
                )
                if isinstance(recent_files, list):
                    self.recent_files = recent_files
            except Exception as e:
                logging.error(str(e))

    def conf_write(self):
        Configuration().parser[ConfigFile.GEOMETRY] = self.get_size()
        Configuration().save()

    def post_show(self):
        if self.file:
            self.open_file(self.file)
        elif Configuration().configuration.get('open_recent_file'):
            if len(self.recent_files):
                self.open_file(self.recent_files[0])

        SIReaderClient().set_call(self.add_sportident_result_from_sireader)
        SportiduinoClient().set_call(self.add_sportiduino_result_from_reader)
        SFRReaderClient().set_call(self.add_sfr_result_from_reader)

        LiveClient().init()
        self._menu_disable(self.current_tab)

    def _setup_ui(self):
        geometry = ConfigFile.GEOMETRY
        x = Configuration().parser.getint(geometry, 'x', fallback=480)
        y = Configuration().parser.getint(geometry, 'y', fallback=320)
        width = Configuration().parser.getint(geometry, 'width', fallback=880)
        height = Configuration().parser.getint(geometry, 'height', fallback=474)

        self.setMinimumSize(QtCore.QSize(480, 320))
        self.setGeometry(x, y, 480, 320)
        self.setWindowIcon(QtGui.QIcon(config.ICON))
        self.set_title()
        self.resize(width, height)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setDockNestingEnabled(False)
        self.setDockOptions(
            QtWidgets.QMainWindow.AllowTabbedDocks
            | QtWidgets.QMainWindow.AnimatedDocks
            | QtWidgets.QMainWindow.ForceTabbedDocks
        )

    def _create_menu(self, parent, actions_list):
        for action_item in actions_list:
            if 'show' in action_item and not action_item['show']:
                return
            if 'type' in action_item:
                if action_item['type'] == 'separator':
                    parent.addSeparator()
            elif 'action' in action_item:
                action = QtWidgets.QAction(self)
                action.setText(action_item['title'])
                action.triggered.connect(
                    self.menu_factory.get_action(action_item['action'])
                )
                if 'shortcut' in action_item:
                    shortcuts = (
                        [action_item['shortcut']]
                        if isinstance(action_item['shortcut'], str)
                        else action_item['shortcut']
                    )
                    action.setShortcuts(shortcuts)
                if 'status_tip' in action_item:
                    action.setStatusTip(action_item['status_tip'])
                if 'tabs' in action_item:
                    self.menu_list_for_disabled.append((action, action_item['tabs']))
                if 'property' in action_item:
                    self.menu_property[action_item['property']] = action
                if (
                    'debug' in action_item and action_item['debug']
                ) or 'debug' not in action_item:
                    parent.addAction(action)
            else:
                menu = QtWidgets.QMenu(parent)
                menu.setTitle(action_item['title'])
                if 'tabs' in action_item:
                    self.menu_list_for_disabled.append((menu, action_item['tabs']))
                self._create_menu(menu, action_item['actions'])
                parent.addAction(menu.menuAction())

    def _setup_menu(self):
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 880, 21))
        self.setMenuBar(self.menubar)
        self._create_menu(self.menubar, menu_list())

    def _setup_statusbar(self):
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)

    def _setup_tab(self):
        self.centralwidget = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.tabwidget = QtWidgets.QTabWidget(self.centralwidget)
        layout.addWidget(self.tabwidget)
        self.setCentralWidget(self.centralwidget)

        self.tabwidget.addTab(persons.Widget(), translate('Competitors'))
        self.tabwidget.addTab(results.Widget(), translate('Race Results'))
        self.tabwidget.addTab(groups.Widget(), translate('Groups'))
        self.tabwidget.addTab(courses.Widget(), translate('Courses'))
        self.tabwidget.addTab(organizations.Widget(), translate('Teams'))
        self.tabwidget.currentChanged.connect(self._menu_disable)

    def _menu_disable(self, tab_index):
        for item in self.menu_list_for_disabled:
            if tab_index not in item[1]:
                item[0].setDisabled(True)
            else:
                item[0].setDisabled(False)

    def get_size(self):
        return {
            'x': self.x() + 8,
            'y': self.y() + 30,
            'width': self.width(),
            'height': self.height(),
        }

    def set_title(self, title=None):
        main_title = '{} {}'.format(config.NAME, config.VERSION)
        if title:
            self.setWindowTitle('{} - {}'.format(title, main_title))
        elif self.file:
            self.set_title(
                '{} [{}]'.format(race().data.get_start_datetime(), self.file)
            )
        else:
            self.setWindowTitle(main_title)

    def statusbar_message(self, msg, msecs=5000):
        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage('', 0)
            self.statusbar.showMessage(msg, msecs)

    def logging(self, text):
        self.log_queue.put(text)

    def select_tab(self, index):
        self.current_tab = index

    @property
    def current_tab(self):
        return self.tabwidget.currentIndex()

    @current_tab.setter
    def current_tab(self, index):
        if index < self.tabwidget.count():
            self.tabwidget.setCurrentIndex(index)
        else:
            logging.error('{} {}'.format(index, translate("Tab doesn't exist")))

    @staticmethod
    def get_configuration():
        return Configuration().configuration

    def init_model(self):
        try:
            self.clear_filters()  # clear filters not to loose filtered data

            table = self.get_person_table()

            if not table:
                return

            table.setModel(PersonMemoryModel())
            table = self.get_result_table()
            table.setModel(ResultMemoryModel())
            table = self.get_group_table()
            table.setModel(GroupMemoryModel())
            table = self.get_course_table()
            table.setModel(CourseMemoryModel())
            table = self.get_organization_table()
            table.setModel(OrganizationMemoryModel())
            Broker().produce('init_model')
        except Exception as e:
            logging.error(str(e))

    def refresh(self):
        logging.debug('Refreshing interface')
        try:
            t = time.time()
            table = self.get_person_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()

            table = self.get_result_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()

            table = self.get_group_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()

            table = self.get_course_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()

            table = self.get_organization_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()
            self.set_title()

            print('Refresh in {:.3f} seconds.'.format(time.time() - t))
            Broker().produce('refresh')
        except Exception as e:
            logging.error(str(e))

    def clear_filters(self, remove_condition=True):
        if self.get_person_table():
            self.get_person_table().model().clear_filter(remove_condition)
            self.get_result_table().model().clear_filter(remove_condition)
            self.get_person_table().model().clear_filter(remove_condition)
            self.get_course_table().model().clear_filter(remove_condition)
            self.get_organization_table().model().clear_filter(remove_condition)

    def apply_filters(self):
        if self.get_person_table():
            self.get_person_table().model().apply_filter()
            self.get_result_table().model().apply_filter()
            self.get_person_table().model().apply_filter()
            self.get_course_table().model().apply_filter()
            self.get_organization_table().model().apply_filter()

    def add_recent_file(self, file):
        self.delete_from_recent_files(file)
        self.recent_files.insert(0, file)
        Configuration().parser[ConfigFile.PATH] = {'recent_files': self.recent_files}

    def delete_from_recent_files(self, file):
        if file in self.recent_files:
            self.recent_files.remove(file)

    def get_table_by_name(self, name):
        return self.findChild(QtWidgets.QTableView, name)

    def get_person_table(self):
        return self.get_table_by_name('PersonTable')

    def get_result_table(self):
        return self.get_table_by_name('ResultTable')

    def get_group_table(self):
        return self.get_table_by_name('GroupTable')

    def get_course_table(self):
        return self.get_table_by_name('CourseTable')

    def get_organization_table(self):
        return self.get_table_by_name('OrganizationTable')

    def get_current_table(self):
        map_ = [
            'PersonTable',
            'ResultTable',
            'GroupTable',
            'CourseTable',
            'OrganizationTable',
        ]
        idx = self.current_tab
        if idx < len(map_):
            return self.get_table_by_name(map_[idx])

    def get_selected_rows(self, table=None):
        if table is None:
            table = self.get_current_table()
        sel_model = table.selectionModel()
        indexes = sel_model.selectedRows()

        ret = []
        for i in indexes:
            orig_index_int = i.row()
            ret.append(orig_index_int)
        return ret

    def add_sportident_result_from_sireader(self, result):
        try:
            assignment_mode = race().get_setting('system_assignment_mode', False)
            if not assignment_mode:
                self.clear_filters(remove_condition=False)
                rg = ResultSportidentGeneration(result)
                if rg.add_result():
                    result = rg.get_result()
                    ResultCalculation(race()).process_results()
                    if race().get_setting('split_printout', False):
                        try:
                            split_printout(result)
                        except NoResultToPrintException as e:
                            logging.error(str(e))
                        except NoPrinterSelectedException as e:
                            logging.error(str(e))
                        except Exception as e:
                            logging.error(str(e))
                    elif result.person and result.person.group:
                        GroupSplits(race(), result.person.group).generate(True)
                    TelegramClient().send_result(result)
                    if result.person:
                        if result.is_status_ok():
                            Sound().ok()
                        else:
                            Sound().fail()
                        if result.person.is_rented_card or RentCards().exists(
                            result.person.card_number
                        ):
                            Sound().rented_card()
            else:
                mv = GlobalAccess().get_main_window()
                selection = mv.get_selected_rows(mv.get_table_by_name('PersonTable'))
                if selection:
                    for i in selection:
                        if i < len(race().persons):
                            cur_person = race().persons[i]
                            if cur_person.card_number:
                                confirm = messageBoxQuestion(
                                    self,
                                    translate('Question'),
                                    translate(
                                        'Are you sure you want to reassign the chip number'
                                    ),
                                    QMessageBox.Yes | QMessageBox.No,
                                )
                                if confirm == QMessageBox.No:
                                    break
                            race().person_card_number(cur_person, result.card_number)
                            break
                else:
                    for person in race().persons:
                        if not person.card_number:
                            _ = race().person_card_number(person, result.card_number)
                            person.is_rented_card = True
                            break
            self.refresh()
        except Exception as e:
            logging.error(str(e))

    def add_sfr_result_from_reader(self, result):
        self.add_sportident_result_from_sireader(result)

    def add_sportiduino_result_from_reader(self, result):
        self.add_sportident_result_from_sireader(result)

    def teamwork(self, command):
        try:
            race().update_data(command.data)
            logging.info(repr(command.data))
            if 'object' in command.data and command.data['object'] in [
                'ResultManual',
                'ResultSportident',
                'ResultSFR',
                'ResultSportiduino',
            ]:
                ResultCalculation(race()).process_results()
            Broker().produce('teamwork_recieving', command.data)
            self.refresh()
        except Exception as e:
            logging.error(str(e))

    # Actions
    def create_file(self, *args, update_data=True):
        file_name = get_save_file_name(
            translate('Create SportOrg file'),
            translate('SportOrg file (*.json)'),
            time.strftime('%Y%m%d'),
        )
        if not file_name:
            try:
                if update_data:
                    new_event([Race()])
                    set_current_race_index(0)
                self.clear_filters(remove_condition=False)
                File(file_name, logging.root, File.JSON).create()
                self.apply_filters()
                self.last_update = time.time()
                self.file = file_name
                self.add_recent_file(self.file)
                self.set_title()
                self.init_model()
            except Exception as e:
                logging.error(str(e))
                QMessageBox.warning(
                    self,
                    translate('Error'),
                    translate('Cannot create file') + ': ' + file_name,
                )
            self.refresh()

    def save_file_as(self):
        self.create_file(update_data=False)

    def save_file(self):
        if self.file:
            try:
                self.clear_filters(remove_condition=False)
                File(self.file, logging.root, File.JSON).save()
                self.apply_filters()
                self.last_update = time.time()
            except Exception as e:
                logging.error(str(e))
        else:
            self.save_file_as()

    def open_file(self, file_name=None):
        if file_name:
            try:
                File(file_name, logging.root, File.JSON).open()
                self.file = file_name
                self.set_title()
                self.add_recent_file(self.file)
                self.init_model()
                self.last_update = time.time()
            except Exception as e:
                logging.exception(str(e))
                self.delete_from_recent_files(file_name)
                QMessageBox.warning(
                    self,
                    translate('Error'),
                    translate('Cannot read file, format unknown') + ': ' + file_name,
                )

    def split_printout_selected(self):
        if self.current_tab != 1:
            logging.warning(translate('No result selected'))
            return
        try:
            indexes = self.get_selected_rows()
            obj = race()
            for index in indexes:
                if index < 0:
                    continue
                if index >= len(obj.results):
                    pass
                self.split_printout(obj.results[index])
        except Exception as e:
            logging.exception(str(e))

    def split_printout(self, result):
        try:
            split_printout(result)
        except NoResultToPrintException as e:
            logging.warning(str(e))
            mes = QMessageBox(self)
            mes.setText(translate('No results to print'))
            mes.exec_()
        except NoPrinterSelectedException as e:
            logging.warning(str(e))
            mes = QMessageBox(self)
            mes.setText(translate('No printer selected'))
            mes.exec_()

    def add_object(self):
        try:
            tab = self.current_tab
            if tab == 0:
                p = race().add_new_person()
                PersonEditDialog(p, True).exec_()
                self.refresh()
            elif tab == 1:
                self.menu_factory.execute('ManualFinishAction')
            elif tab == 2:
                g = race().add_new_group()
                GroupEditDialog(g, True).exec_()
                self.refresh()
            elif tab == 3:
                c = race().add_new_course()
                CourseEditDialog(c, True).exec_()
                self.refresh()
            elif tab == 4:
                o = race().add_new_organization()
                OrganizationEditDialog(o, True).exec_()
                self.refresh()
        except Exception as e:
            logging.error(str(e))

    def delete_object(self):
        try:
            if self.current_tab not in range(5):
                return
            self._delete_object()
        except Exception as e:
            logging.error(str(e))

    def _delete_object(self):
        indexes = self.get_selected_rows()
        if not len(indexes):
            return

        confirm = messageBoxQuestion(
            self,
            translate('Question'),
            translate('Please confirm'),
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.No:
            return
        tab = self.current_tab
        res = []
        if tab == 0:
            res = race().delete_persons(indexes)
            ResultCalculation(race()).process_results()
            self.refresh()
        elif tab == 1:
            res = race().delete_results(indexes)
            ResultCalculation(race()).process_results()
            self.refresh()
        elif tab == 2:
            try:
                res = race().delete_groups(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(
                    self.get_group_table(),
                    translate('Error'),
                    translate('Cannot remove group'),
                )
            self.refresh()
        elif tab == 3:
            try:
                res = race().delete_courses(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(
                    self.get_course_table(),
                    translate('Error'),
                    translate('Cannot remove course'),
                )
            self.refresh()
        elif tab == 4:
            try:
                res = race().delete_organizations(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(
                    self.get_organization_table(),
                    translate('Error'),
                    translate('Cannot remove organization'),
                )
            self.refresh()
