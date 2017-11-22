import ast
import configparser
import logging
import time

from PyQt5 import QtCore, QtGui, QtWidgets, Qt
from PyQt5.QtWidgets import QMainWindow, QTableView, QMessageBox

from sportorg import config
from sportorg.app.gui.dialogs.about import AboutDialog
from sportorg.app.gui.dialogs.entry_filter import DialogFilter
from sportorg.app.gui.dialogs.event_properties import EventPropertiesDialog
from sportorg.app.gui.dialogs.file_dialog import get_open_file_name, get_save_file_name
from sportorg.app.gui.dialogs.number_change import NumberChangeDialog
from sportorg.app.gui.dialogs.print_properties import PrintPropertiesDialog
from sportorg.app.gui.dialogs.report_dialog import ReportDialog
from sportorg.app.gui.dialogs.settings import SettingsDialog
from sportorg.app.gui.dialogs.sportident_properties import SportidentPropertiesDialog
from sportorg.app.gui.dialogs.start_chess_dialog import StartChessDialog
from sportorg.app.gui.dialogs.start_preparation import StartPreparationDialog
from sportorg.app.gui.dialogs.start_report_dialog import StartReportDialog
from sportorg.app.gui.global_access import GlobalAccess
from sportorg.app.gui.menu import menu_list
from sportorg.app.gui.post_init import POST_INIT
from sportorg.app.gui.tabs import start_preparation, groups, teams, race_results, courses
from sportorg.app.gui.toolbar import toolbar_list
from sportorg.app.models.memory import Race, event as races, race, Config as Configuration
from sportorg.app.models.memory_model import PersonMemoryModel, ResultMemoryModel, GroupMemoryModel, \
    CourseMemoryModel, TeamMemoryModel
from sportorg.app.models.split_calculation import split_printout
from sportorg.app.models.start_preparation import guess_courses_for_groups, guess_corridors_for_groups
from sportorg.app.modules.backup import backup
from sportorg.app.modules.ocad import ocad
from sportorg.app.modules.sportident import sportident
from sportorg.app.modules.winorient import winorient
from sportorg.core import event
from sportorg.core.app import App
from sportorg.language import _


class MainWindow(QMainWindow, App):
    def __init__(self, argv=None):
        super().__init__()
        self.recent_files = []
        try:
            self.file = argv[1]
            self.add_recent_file(self.file)
        except IndexError:
            self.file = None
        self.conf = configparser.ConfigParser()
        GlobalAccess().set_main_window(self)
        backup.init()

    def show_window(self):
        try:
            self.conf_read()
        except Exception as e:
            logging.error(e)
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_tab()
        self._setup_statusbar()
        self._setup_system_tray_icon()
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
        self.conf.read(config.CONFIG_INI)
        if self.conf.has_section(config.ConfigFile.CONFIGURATION):
            for option in self.conf.options(config.ConfigFile.CONFIGURATION):
                Configuration.set_parse(
                    option, self.conf.get(config.ConfigFile.CONFIGURATION, option, fallback=Configuration.get(option)))

        if self.conf.has_section(config.ConfigFile.PATH):
            recent_files = ast.literal_eval(self.conf.get(config.ConfigFile.PATH, 'recent_files', fallback='[]'))
            if isinstance(recent_files, list):
                self.recent_files = recent_files

    def conf_write(self):
        self.conf[config.ConfigFile.GEOMETRY] = {
            'x': self.x() + 8,
            'y': self.y() + 30,
            'width': self.width(),
            'height': self.height(),
        }
        self.conf[config.ConfigFile.CONFIGURATION] = Configuration.get_all()
        self.conf[config.ConfigFile.PATH] = {
            'recent_files': self.recent_files
        }
        with open(config.CONFIG_INI, 'w') as configfile:
            self.conf.write(configfile)

    def post_show(self):
        if self.file:
            self.open_file(self.file)
        elif Configuration.get('open_recent_file'):
            if len(self.recent_files):
                self.open_file(self.recent_files[0])

        if Configuration.get('autoconnect'):
            self.sportident_connect()

        for init in POST_INIT:
            init()

    def _setup_ui(self):
        geometry = config.ConfigFile.GEOMETRY
        x = self.conf.getint('%s' % geometry, 'x', fallback=480)
        y = self.conf.getint(geometry, 'y', fallback=320)
        width = self.conf.getint(geometry, 'width', fallback=880)
        height = self.conf.getint(geometry, 'height', fallback=474)

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
        self.menu_property = {}
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 880, 21))
        self.setMenuBar(self.menubar)
        self._create_menu(self.menubar, menu_list())

    def _setup_toolbar(self):
        layout = QtWidgets.QVBoxLayout()
        self.toolbar = self.addToolBar(_('Toolbar'))
        self.toolbar_property = {}
        for tb in toolbar_list():
            tb_action = QtWidgets.QAction(QtGui.QIcon(tb[0]), tb[1], self)
            tb_action.triggered.connect(tb[2])
            if len(tb) == 4:
                self.toolbar_property[tb[3]] = tb_action
            self.toolbar.addAction(tb_action)

        self.setLayout(layout)

    def _setup_statusbar(self):
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar_message(_("it works!"))

    def _setup_system_tray_icon(self):
        self.system_tray_icon = Qt.QSystemTrayIcon(self)
        self.system_tray_icon.show()

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

    def set_title(self, title=None):
        main_title = '{} {}'.format(_(config.NAME), config.VERSION)
        if title:
            self.setWindowTitle('{} - {}'.format(title, main_title))
        else:
            self.setWindowTitle(main_title)

    def create_file(self, file_name=None, update_data=True):

        # TODO: save changes in current file

        file_name = get_save_file_name(_('Create SportOrg file'), _("SportOrg file (*.sportorg)"),
                                       str(time.strftime("%Y%m%d")))
        if file_name is not '':
            self.set_title(file_name)
            try:
                super().create_file(file_name)
            except Exception as e:
                logging.exception(str(e))
            # remove data
            if update_data:
                races[0] = Race()
            self.add_recent_file(self.file)
            self.refresh()

    def save_file_as(self):
        self.create_file(None, False)
        if self.file is not None:
            self.save_file()

    def save_file(self):
        if self.file is not None:
            try:
                super().save_file()
            except Exception as e:
                logging.exception(str(e))
        else:
            self.save_file_as()

    def open_file(self, file_name=None):
        if file_name:
            try:
                super().open_file(file_name)
                self.set_title(file_name)
                self.add_recent_file(self.file)
                self.init_model()
            except Exception as e:
                logging.exception(str(e))
                self.delete_from_recent_files(file_name)
                QMessageBox.warning(self,
                                     _('Error'),
                                     _('Cannot read file, format unknown') + ': ' + file_name)

    def open_file_dialog(self):
        file_name = get_open_file_name(_('Open SportOrg file'), _("SportOrg file (*.sportorg)"))
        self.open_file(file_name)

    def system_message(self, title, content, icon=None, msecs=5000):
        if icon is None:
            icon = 0
        icon_val = {
            'context': Qt.QSystemTrayIcon.Context,
            'critical': Qt.QSystemTrayIcon.Critical,
            'doubleclick': Qt.QSystemTrayIcon.DoubleClick,
            'information': Qt.QSystemTrayIcon.Information,
            'middleclick': Qt.QSystemTrayIcon.MiddleClick,
            'noicon': Qt.QSystemTrayIcon.NoIcon,
            'trigger': Qt.QSystemTrayIcon.Trigger,
            'unknown': Qt.QSystemTrayIcon.Unknown,
            'warning': Qt.QSystemTrayIcon.Warning
        }
        self.system_tray_icon.showMessage(title, content, icon_val[icon] if icon in icon_val else icon, msecs)

    def statusbar_message(self, msg, msecs=5000):
        self.statusbar.showMessage('', 0)
        self.statusbar.showMessage(msg, msecs)

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
        return Configuration

    def add_recent_file(self, file):
        self.delete_from_recent_files(file)
        self.recent_files.insert(0, file)

    def delete_from_recent_files(self, file):
        if file in self.recent_files:
            self.recent_files.remove(file)

    @staticmethod
    def settings_dialog():
        try:
            SettingsDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def filter_dialog():
        try:
            table = GlobalAccess().get_current_table()
            ex = DialogFilter(table)
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

    def split_printout(self):
        if self.current_tab != 1:
            self.statusbar_message(_('No result selected'))
            return
        try:
            obj = race()

            table = GlobalAccess().get_result_table()
            assert isinstance(table, QTableView)
            index = table.currentIndex().row()
            if index < 0:
                index = 0
            if index >= len(obj.results):
                mes = QMessageBox()
                mes.setText(_('No results to print'))
                mes.exec()
                return

            split_printout(obj.results[index])

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

    @staticmethod
    def guess_courses():
        try:
            guess_courses_for_groups()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def guess_corridors():
        try:
            guess_corridors_for_groups()
        except Exception as e:
            logging.exception(str(e))

    def manual_finish(self):
        try:
            race().add_new_result()
            GlobalAccess().get_result_table().model().init_cache()
            GlobalAccess().get_main_window().refresh()
            self.statusbar_message(_('Manual finish'))
            GlobalAccess().auto_save()
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
    def create_chess_dialog():
        try:
            ex = StartChessDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def create_object():
        GlobalAccess().add_object()

    @staticmethod
    def delete_object():
        try:
            GlobalAccess().delete_object()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def init_model():
        try:
            GlobalAccess().clear_filters()  # clear filters not to loose filtered data

            table = GlobalAccess().get_person_table()
            table.setModel(PersonMemoryModel())
            table = GlobalAccess().get_result_table()
            table.setModel(ResultMemoryModel())
            table = GlobalAccess().get_group_table()
            table.setModel(GroupMemoryModel())
            table = GlobalAccess().get_course_table()
            table.setModel(CourseMemoryModel())
            table = GlobalAccess().get_organization_table()
            table.setModel(TeamMemoryModel())
            event.event('init_model')
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def refresh():
        logging.debug('Refreshing interface')
        try:
            table = GlobalAccess().get_person_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()

            table = GlobalAccess().get_result_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()

            table = GlobalAccess().get_group_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()

            table = GlobalAccess().get_course_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()

            table = GlobalAccess().get_organization_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()
            event.event('refresh')
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def sportident_settings_dialog():
        try:
            SportidentPropertiesDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def sportident_connect():
        try:
            sportident.start_reader()
        except Exception as e:
            logging.exception(str(e))

    def import_wo_csv(self):
        file_name = get_open_file_name(_('Open CSV Winorient file'), _("CSV Winorient (*.csv)"))
        if file_name is not '':
            try:
                winorient.import_csv(file_name)
            except Exception as e:
                logging.exception(str(e))
                QMessageBox.question(None,
                                     _('Error'),
                                     _('Import error') + ': ' + file_name)
            self.init_model()

    def import_wo_wdb(self):
        file_name = get_open_file_name(_('Open WDB Winorient file'), _("WDB Winorient (*.wdb)"))
        if file_name is not '':
            try:
                winorient.import_wo_wdb(file_name)
            except Exception as e:
                logging.exception(str(e))
            self.init_model()

    @staticmethod
    def export_wo_wdb():
        file_name = get_save_file_name(_('Save As WDB file'), _("WDB file (*.wdb)"),
                                       '{}_sportorg_export'.format(time.strftime("%Y%m%d")))
        if file_name is not '':
            try:
                winorient.export_wo_wdb(file_name)
            except Exception as e:
                logging.exception(str(e))

    def import_txt_v8(self):
        file_name = get_open_file_name(_('Open Ocad txt v8 file'), _("Ocad classes v8 (*.txt)"))
        if file_name is not '':
            try:
                ocad.import_txt_v8(file_name)
            except Exception as e:
                logging.exception(str(e))
                QMessageBox.question(None,
                                     _('Error'),
                                     _('Import error') + ': ' + file_name)

            self.init_model()

    def about_dialog(self):
        try:
            AboutDialog().exec()
        except Exception as e:
            logging.exception(str(e))
