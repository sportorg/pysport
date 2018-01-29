import ast
import logging
import time

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QModelIndex, QItemSelectionModel
from PyQt5.QtWidgets import QMainWindow, QTableView, QMessageBox, QApplication

from sportorg.core.otime import OTime
from sportorg.gui.dialogs.bib_report_dialog import BibReportDialog
from sportorg.gui.dialogs.live_dialog import LiveDialog
from sportorg.gui.dialogs.not_start_dialog import NotStartDialog
from sportorg.gui.dialogs.relay_number_dialog import RelayNumberDialog
from sportorg.gui.dialogs.search_dialog import SearchDialog
from sportorg.gui.dialogs.start_time_change_dialog import StartTimeChangeDialog
from sportorg.gui.dialogs.team_report_dialog import TeamReportDialog
from sportorg.gui.dialogs.team_results_report_dialog import TeamResultsReportDialog
from sportorg.gui.dialogs.text_io import TextExchangeDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.libs.winorient.wdb import write_wdb
from sportorg.models.memory import Race, event as races, race, ResultStatus, NotEmptyException

from sportorg import config
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.result_checker import ResultChecker
from sportorg.modules.backup.file import File
from sportorg.modules.iof import iof_xml
from sportorg.modules.live.orgeo import OrgeoClient
from sportorg.modules.ocad import ocad
from sportorg.modules.ocad.ocad import OcadImportException
from sportorg.modules.printing.model import NoResultToPrintException, split_printout, NoPrinterSelectedException
from sportorg.modules import testing
from sportorg.modules.configs.configs import Config as Configuration, ConfigFile
from sportorg.modules.sportident.result_generation import ResultSportidentGeneration
from sportorg.modules.sportident.sireader import SIReaderClient
from sportorg.modules.winorient import winorient
from sportorg.core import event
from sportorg.gui.dialogs.about import AboutDialog
from sportorg.gui.dialogs.entry_filter import DialogFilter
from sportorg.gui.dialogs.event_properties import EventPropertiesDialog
from sportorg.gui.dialogs.file_dialog import get_open_file_name, get_save_file_name
from sportorg.gui.dialogs.number_change import NumberChangeDialog
from sportorg.gui.dialogs.print_properties import PrintPropertiesDialog
from sportorg.gui.dialogs.report_dialog import ReportDialog
from sportorg.gui.dialogs.settings import SettingsDialog
from sportorg.gui.dialogs.timekeeping_properties import TimekeepingPropertiesDialog
from sportorg.gui.dialogs.start_chess_dialog import StartChessDialog
from sportorg.gui.dialogs.start_preparation import StartPreparationDialog
from sportorg.gui.dialogs.start_report_dialog import StartReportDialog
from sportorg.gui.menu.menu import menu_list
from sportorg.gui.tabs import start_preparation, groups, teams, race_results, courses, log
from sportorg.gui.tabs.memory_model import PersonMemoryModel, ResultMemoryModel, GroupMemoryModel, \
    CourseMemoryModel, TeamMemoryModel
from sportorg.gui.toolbar import toolbar_list
from sportorg.language import _
from sportorg.models.start.start_preparation import guess_courses_for_groups, guess_corridors_for_groups
from sportorg.modules.winorient.wdb import WDBImportError, WinOrientBinary


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
        self.recent_files = []
        self.menu_property = {}
        self.toolbar_property = {}
        try:
            self.file = argv[1]
            self.add_recent_file(self.file)
        except IndexError:
            self.file = None
        GlobalAccess().set_main_window(self)

        handler = ConsolePanelHandler(self)
        logging.root.addHandler(handler)

    def show_window(self):
        try:
            self.conf_read()
        except Exception as e:
            logging.error(e)
        self._setup_ui()
        self._setup_menu()
        if Configuration().configuration.get('show_toolbar'):
            self._setup_toolbar()
        self._setup_tab()
        self._setup_statusbar()
        self.show()
        self.post_show()

    def close(self):
        self.conf_write()
        """
        :event: close
        """
        event.event('close')

    def closeEvent(self, _event):
        self.close()
        _event.accept()

    def resizeEvent(self, e):
        event.event('resize', {
            'x': self.x() + 8,
            'y': self.y() + 30,
            'width': self.width(),
            'height': self.height(),
        })

    def conf_read(self):
        Configuration().read()
        if Configuration().parser.has_section(ConfigFile.PATH):
            recent_files = ast.literal_eval(Configuration().parser.get(ConfigFile.PATH, 'recent_files', fallback='[]'))
            if isinstance(recent_files, list):
                self.recent_files = recent_files

    def conf_write(self):
        Configuration().parser[ConfigFile.GEOMETRY] = {
            'x': self.x() + 8,
            'y': self.y() + 30,
            'width': self.width(),
            'height': self.height(),
        }
        Configuration().parser[ConfigFile.PATH] = {
            'recent_files': self.recent_files
        }
        Configuration().save()

    def post_show(self):
        if self.file:
            self.open_file(self.file)
        elif Configuration().configuration.get('open_recent_file'):
            if len(self.recent_files):
                self.open_file(self.recent_files[0])

        if Configuration().configuration.get('autoconnect'):
            self.sportident_connect()

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
        self.setDockOptions(QtWidgets.QMainWindow.AllowTabbedDocks
                            | QtWidgets.QMainWindow.AnimatedDocks
                            | QtWidgets.QMainWindow.ForceTabbedDocks)

    def _create_menu(self, parent, actions_list):
        for action_item in actions_list:
            if 'show' in action_item and not action_item['show']:
                return
            if 'type' in action_item:
                if action_item['type'] == 'separator':
                    parent.addSeparator()
            elif 'action' in action_item:
                action = QtWidgets.QAction(self)
                parent.addAction(action)
                action.setText(action_item['title'])
                action.triggered.connect(action_item['action'])
                if 'shortcut' in action_item:
                    action.setShortcut(action_item['shortcut'])
                if 'icon' in action_item:
                    action.setIcon(QtGui.QIcon(action_item['icon']))
                if 'status_tip' in action_item:
                    action.setStatusTip(action_item['status_tip'])
                if 'property' in action_item:
                    self.menu_property[action_item['property']] = action
            else:
                menu = QtWidgets.QMenu(parent)
                menu.setTitle(action_item['title'])
                self._create_menu(menu, action_item['actions'])
                parent.addAction(menu.menuAction())

    def _setup_menu(self):
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 880, 21))
        self.setMenuBar(self.menubar)
        self._create_menu(self.menubar, menu_list())

    def _setup_toolbar(self):
        self.toolbar = self.addToolBar(_('Toolbar'))
        for tb in toolbar_list():
            tb_action = QtWidgets.QAction(QtGui.QIcon(tb[0]), tb[1], self)
            tb_action.triggered.connect(tb[2])
            if len(tb) == 4:
                self.toolbar_property[tb[3]] = tb_action
            self.toolbar.addAction(tb_action)

    def _setup_statusbar(self):
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)

    def _setup_tab(self):
        self.centralwidget = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.tabwidget = QtWidgets.QTabWidget(self.centralwidget)
        layout.addWidget(self.tabwidget)
        self.setCentralWidget(self.centralwidget)

        self.tabwidget.addTab(start_preparation.Widget(), _("Start Preparation"))
        self.tabwidget.addTab(race_results.Widget(), _("Race Results"))
        self.tabwidget.addTab(groups.Widget(), _("Groups"))
        self.tabwidget.addTab(courses.Widget(), _("Courses"))
        self.tabwidget.addTab(teams.Widget(), _("Teams"))
        self.logging_tab = log.Widget()
        self.tabwidget.addTab(self.logging_tab, _("Logs"))

    def set_title(self, title=None):
        main_title = '{} {}'.format(_(config.NAME), config.VERSION)
        if title:
            self.setWindowTitle('{} - {}'.format(title, main_title))
        else:
            self.setWindowTitle(main_title)

    def statusbar_message(self, msg, msecs=5000):
        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage('', 0)
            self.statusbar.showMessage(msg, msecs)

    def logging(self, text):
        self.statusbar_message(text)
        if hasattr(self, 'logging_tab'):
            self.logging_tab.write(text)

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
            logging.error("{} {}".format(index, _("Tab doesn't exist")))

    @staticmethod
    def get_configuration():
        return Configuration().configuration

    def init_model(self):
        try:
            self.clear_filters()  # clear filters not to loose filtered data

            table = self.get_person_table()
            table.setModel(PersonMemoryModel())
            table = self.get_result_table()
            table.setModel(ResultMemoryModel())
            table = self.get_group_table()
            table.setModel(GroupMemoryModel())
            table = self.get_course_table()
            table.setModel(CourseMemoryModel())
            table = self.get_organization_table()
            table.setModel(TeamMemoryModel())
            event.event('init_model')
        except Exception as e:
            logging.exception(str(e))

    def refresh(self):
        logging.debug('Refreshing interface')
        try:
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
            event.event('refresh')
        except Exception as e:
            logging.exception(str(e))

    def clear_filters(self, remove_condition=True):
        self.get_person_table().model().clear_filter(remove_condition)
        self.get_result_table().model().clear_filter(remove_condition)
        self.get_person_table().model().clear_filter(remove_condition)
        self.get_course_table().model().clear_filter(remove_condition)
        self.get_organization_table().model().clear_filter(remove_condition)

        self.get_person_table().model().clear_search(remove_condition)
        self.get_result_table().model().clear_search(remove_condition)
        self.get_person_table().model().clear_search(remove_condition)
        self.get_course_table().model().clear_search(remove_condition)
        self.get_organization_table().model().clear_search(remove_condition)

    def apply_filters(self):
        self.get_person_table().model().apply_filter()
        self.get_result_table().model().apply_filter()
        self.get_person_table().model().apply_filter()
        self.get_course_table().model().apply_filter()
        self.get_organization_table().model().apply_filter()

    def auto_save(self):
        if not self.get_configuration().get('autosave'):
            return
        if self.file:
            self.save_file()
            logging.info(_('Auto save'))
        else:
            logging.warning(_('No file to auto save'))

    def add_recent_file(self, file):
        self.delete_from_recent_files(file)
        self.recent_files.insert(0, file)

    def delete_from_recent_files(self, file):
        if file in self.recent_files:
            self.recent_files.remove(file)

    # Actions
    def create_file(self, *args, update_data=True):
        file_name = get_save_file_name(
            _('Create SportOrg file'),
            _('SportOrg file (*.sportorg)'),
            time.strftime("%Y%m%d")
        )
        if file_name is not '':
            try:
                if update_data:
                    races[0] = Race()
                self.clear_filters(remove_condition=False)
                File(file_name, logging.root).create()
                self.file = file_name
                self.add_recent_file(self.file)
                self.set_title(file_name)
                self.init_model()
            except Exception as e:
                logging.exception(str(e))
                QMessageBox.warning(self, _('Error'), _('Cannot create file') + ': ' + file_name)
            self.refresh()

    def save_file_as(self):
        self.create_file(update_data=False)
        if self.file is not None:
            self.save_file()

    def save_file(self):
        if self.file is not None:
            try:
                self.clear_filters(remove_condition=False)
                File(self.file, logging.root).save()
            except Exception as e:
                logging.exception(str(e))
        else:
            self.save_file_as()

    def open_file(self, file_name=None):
        if file_name:
            try:
                File(file_name, logging.root).open()
                self.file = file_name
                self.set_title(file_name)
                self.add_recent_file(self.file)
                self.init_model()
            except Exception as e:
                logging.exception(str(e))
                self.delete_from_recent_files(file_name)
                QMessageBox.warning(self, _('Error'), _('Cannot read file, format unknown') + ': ' + file_name)

    def open_file_dialog(self):
        file_name = get_open_file_name(_('Open SportOrg file'), _("SportOrg file (*.sportorg)"))
        self.open_file(file_name)

    @staticmethod
    def settings_dialog():
        try:
            SettingsDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    def filter_dialog(self):
        try:
            if self.current_tab not in range(2):
                return
            table = self.get_current_table()
            ex = DialogFilter(table)
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    def search_dialog(self):
        if self.current_tab not in range(5):
            return
        try:
            table = self.get_current_table()
            ex = SearchDialog(table)
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def report_dialog():
        try:
            ex = ReportDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def team_results_report_dialog():
        try:
            ex = TeamResultsReportDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    def split_printout_selected(self):
        if self.current_tab != 1:
            logging.warning(_('No result selected'))
            return
        try:
            obj = race()

            table = self.get_result_table()
            assert isinstance(table, QTableView)
            index = table.currentIndex().row()
            if index < 0:
                index = 0
            if index >= len(obj.results):
                mes = QMessageBox()
                mes.setText(_('No results to print'))
                mes.exec()
                return
            self.split_printout(obj.results[index])
        except Exception as e:
            logging.exception(str(e))

    def split_printout(self, result):
        try:
            split_printout(result)
        except NoResultToPrintException as e:
            logging.warning(str(e))
            mes = QMessageBox(self)
            mes.setText(_('No results to print'))
            mes.exec()
        except NoPrinterSelectedException as e:
            logging.warning(str(e))
            mes = QMessageBox(self)
            mes.setText(_('No printer selected'))
            mes.exec()

    def change_status(self):
        if self.current_tab != 1:
            logging.warning(_('No result selected'))
            return
        try:
            obj = race()

            status_dict = {
                ResultStatus.NONE: ResultStatus.OK,
                ResultStatus.OK: ResultStatus.DISQUALIFIED,
                ResultStatus.DISQUALIFIED: ResultStatus.DID_NOT_START,
                ResultStatus.DID_NOT_START: ResultStatus.DID_NOT_FINISH,
                ResultStatus.DID_NOT_FINISH: ResultStatus.OK,
            }

            table = self.get_result_table()
            assert isinstance(table, QTableView)
            index = table.currentIndex().row()
            if index < 0:
                index = 0
            if index >= len(obj.results):
                mes = QMessageBox()
                mes.setText(_('No results to change status'))
                mes.exec()
                return
            result = obj.results[index]
            result.status = status_dict[result.status]
            self.refresh()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def not_start_dialog():
        try:
            ex = NotStartDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def event_settings_dialog():
        try:
            ex = EventPropertiesDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def start_preparation_dialog():
        try:
            StartPreparationDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def print_settings_dialog():
        try:
            PrintPropertiesDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def number_change_dialog():
        try:
            obj = NumberChangeDialog()
            obj.exec()
        except Exception as e:
            logging.exception(str(e))

    def guess_courses(self):
        try:
            guess_courses_for_groups()
            self.refresh()
        except Exception as e:
            logging.exception(str(e))

    def guess_corridors(self):
        try:
            guess_corridors_for_groups()
            self.refresh()
        except Exception as e:
            logging.exception(str(e))

    def relay_number_assign(self):
        try:
            obj = race()
            if obj.get_setting('relay_number_assign', False):
                obj.set_setting('relay_number_assign', False)
                QApplication.restoreOverrideCursor()
            else:
                obj.set_setting('relay_number_assign', True)
                QApplication.setOverrideCursor(QtCore.Qt.PointingHandCursor)
                RelayNumberDialog().exec()
            self.refresh()
        except Exception as e:
            logging.exception(str(e))

    def start_time_change(self):
        try:
            StartTimeChangeDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    def manual_finish(self):
        try:
            result = race().new_result()
            race().add_new_result(result)
            logging.info('Manual finish')
            self.get_result_table().model().init_cache()
            self.refresh()
            self.auto_save()
        except Exception as e:
            logging.exception(str(e))

    def sportident_result(self):
        try:
            result = race().new_sportident_result()
            race().add_new_result(result)
            logging.info('SPORTident result')
            self.get_result_table().model().init_cache()
            self.refresh()
            self.auto_save()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def create_start_protocol_dialog():
        try:
            ex = StartReportDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def create_team_protocol_dialog():
        try:
            ex = TeamReportDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def create_chess_dialog():
        try:
            ex = StartChessDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def bib_report_dialog():
        try:
            ex = BibReportDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def live_dialog():
        try:
            ex = LiveDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def live_send_start_list():
        try:
            OrgeoClient().send_start_list()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def live_send_results():
        try:
            OrgeoClient().send_results()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def live_resend_results():
        try:
            OrgeoClient().clear()
            OrgeoClient().send_results()
        except Exception as e:
            logging.exception(str(e))

    def create_object(self):
        self.add_object()

    def delete_object(self):
        if self.current_tab not in range(5):
            return
        try:
            self.delete_object()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def timekeeping_settings_dialog():
        try:
            TimekeepingPropertiesDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    def sportident_connect(self):
        try:
            SIReaderClient().set_call(self.add_sportident_result_from_sireader).start()
        except Exception as e:
            logging.exception(str(e))

    def add_sportident_result_from_sireader(self, result):
        try:
            assignment_mode = race().get_setting('sportident_assignment_mode', False)
            if not assignment_mode:
                self.clear_filters(remove_condition=False)
                ResultSportidentGeneration(result).add_result()
                ResultCalculation(race()).process_results()
                if race().get_setting('split_printout', False):
                    try:
                        split_printout(result)
                    except NoResultToPrintException as e:
                        logging.error(str(e))
                    except NoPrinterSelectedException as e:
                        logging.error(str(e))
                    except Exception as e:
                        logging.exception(str(e))
                self.auto_save()
                OrgeoClient().send_results()
            else:
                for person in race().persons:
                    if not person.sportident_card:
                        race().person_sportident_card(person, result.sportident_card)
                        person.is_rented_sportident_card = True
                        break
            self.refresh()
        except Exception as e:
            logging.exception(str(e))

    def import_wo_csv(self):
        file_name = get_open_file_name(_('Open CSV Winorient file'), _("CSV Winorient (*.csv)"))
        if file_name is not '':
            try:
                winorient.import_csv(file_name)
            except Exception as e:
                logging.exception(str(e))
                QMessageBox.warning(self, _('Error'), _('Import error') + ': ' + file_name)
            self.init_model()

    def import_wo_wdb(self):
        file_name = get_open_file_name(_('Open WDB Winorient file'), _("WDB Winorient (*.wdb)"))
        if file_name is not '':
            try:
                winorient.import_wo_wdb(file_name)
            except WDBImportError as e:
                logging.exception(str(e))
                QMessageBox.warning(self, _('Error'), _('Import error') + ': ' + file_name)
            self.init_model()

    def export_wo_wdb(self):
        file_name = get_save_file_name(_('Save As WDB file'), _("WDB file (*.wdb)"),
                                       '{}_sportorg_export'.format(time.strftime("%Y%m%d")))
        if file_name is not '':
            try:
                wb = WinOrientBinary()

                self.clear_filters(False)
                wdb_object = wb.export()
                self.apply_filters()

                write_wdb(wdb_object, file_name)
            except Exception as e:
                logging.exception(str(e))
                QMessageBox.warning(self, _('Error'), _('Export error') + ': ' + file_name)

    def import_txt_v8(self):
        file_name = get_open_file_name(_('Open Ocad txt v8 file'), _("Ocad classes v8 (*.txt)"))
        if file_name is not '':
            try:
                ocad.import_txt_v8(file_name)
            except OcadImportException as e:
                logging.exception(str(e))
                QMessageBox.warning(self, _('Error'), _('Import error') + ': ' + file_name)

            self.init_model()

    def text_exchange(self):
        TextExchangeDialog().exec()
        self.refresh()

    @staticmethod
    def testing():
        try:
            testing.test()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def about_dialog():
        try:
            AboutDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    def export_iof_result_list(self):
        file_name = get_save_file_name(_('Save As IOF xml'), _("IOF xml (*.xml)"),
                                       '{}_resultList'.format(time.strftime("%Y%m%d")))
        if file_name is not '':
            try:
                iof_xml.export_result_list(file_name)
            except Exception as e:
                logging.exception(str(e))
                QMessageBox.warning(self, _('Error'), _('Export error') + ': ' + file_name)

    def get_table_by_name(self, name):
        return self.findChild(QtWidgets.QTableView, name)

    def get_person_table(self):
        return self.get_table_by_name('EntryTable')

    def get_result_table(self):
        return self.get_table_by_name('ResultTable')

    def get_group_table(self):
        return self.get_table_by_name('GroupTable')

    def get_course_table(self):
        return self.get_table_by_name('CourseTable')

    def get_organization_table(self):
        return self.get_table_by_name('TeamTable')

    def get_current_table(self):
        map_ = ['EntryTable', 'ResultTable', 'GroupTable', 'CourseTable', 'TeamTable']
        idx = self.current_tab
        if idx < len(map_):
            return self.get_table_by_name(map_[idx])

    def get_selected_rows(self):
        table = self.get_current_table()
        assert isinstance(table, QTableView)
        sel_model = table.selectionModel()
        assert isinstance(sel_model, QItemSelectionModel)
        indexes = sel_model.selectedRows()

        ret = []
        for i in indexes:
            assert isinstance(i, QModelIndex)
            orig_index_int = i.row()
            ret.append(orig_index_int)
        return ret

    def delete_object(self):
        indexes = self.get_selected_rows()
        if not len(indexes):
            return

        confirm = QMessageBox.question(self,
                                       _('Question'),
                                       _('Please confirm'),
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.No:
            return
        tab = self.current_tab

        if tab == 0:
            race().delete_persons(indexes)
            # recalculate places
            ResultCalculation(race()).process_results()
            self.refresh()
        elif tab == 1:
            race().delete_results(indexes)
            # recalculate places
            ResultCalculation(race()).process_results()
            self.refresh()
        elif tab == 2:
            try:
                race().delete_groups(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(self.get_group_table(),
                                     _('Error'),
                                     _('Cannot remove group'))
            self.refresh()
        elif tab == 3:
            try:
                race().delete_courses(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(self.get_course_table(),
                                     _('Error'),
                                     _('Cannot remove course'))
            self.refresh()
        elif tab == 4:
            try:
                race().delete_organizations(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(self.get_organization_table(),
                                     _('Error'),
                                     _('Cannot remove organization'))
            self.refresh()

    def add_object(self):
        try:
            tab = self.current_tab
            if tab == 0:
                race().add_new_person()
                self.get_person_table().model().init_cache()
            elif tab == 1:
                self.manual_finish()
            elif tab == 2:
                race().add_new_group()
                self.get_person_table().model().init_cache()
            elif tab == 3:
                race().add_new_course()
                self.get_course_table().model().init_cache()
            elif tab == 4:
                race().add_new_organization()
                self.get_organization_table().model().init_cache()
            self.refresh()
        except Exception as e:
            logging.exception(str(e))

    def rechecking(self):
        try:
            logging.debug('Rechecking start')
            for result in race().results:
                if result.person is not None:
                    ResultChecker.checking(result)
            logging.debug('Rechecking finish')
            ResultCalculation(race()).process_results()
            self.refresh()
        except Exception as e:
            logging.exception(str(e))

    def penalty_calculation(self):
        try:
            logging.debug('Penalty calculation start')
            for result in race().results:
                if result.person is not None:
                    ResultChecker.calculate_penalty(result)
            logging.debug('Penalty calculation finish')
            ResultCalculation(race()).process_results()
            self.refresh()
        except Exception as e:
            logging.exception(str(e))

    def penalty_removing(self):
        try:
            logging.debug('Penalty removing start')
            for result in race().results:
                result.penalty_time = OTime(msec=0)
                result.penalty_laps = 0
            logging.debug('Penalty removing finish')
            ResultCalculation(race()).process_results()
            self.refresh()
        except Exception as e:
            logging.exception(str(e))
