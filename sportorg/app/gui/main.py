import configparser
import logging.config
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
from sportorg.app.gui.tabs import start_preparation, groups, teams, race_results, courses
from sportorg.app.gui.toolbar import toolbar_list
from sportorg.app.models.memory import Race, event as races, race, Config as Configuration
from sportorg.app.models import result_generation
from sportorg.app.models.memory_model import PersonMemoryModel, ResultMemoryModel, GroupMemoryModel, \
    CourseMemoryModel, TeamMemoryModel
from sportorg.app.models.split_calculation import GroupSplits
from sportorg.app.models.start_preparation import guess_courses_for_groups, guess_corridors_for_groups
from sportorg.app.modules.backup import backup
from sportorg.app.modules.ocad import ocad
from sportorg.app.modules.printing.printing import print_html
from sportorg.app.modules.sportident import sportident
from sportorg.app.modules.winorient import winorient
from sportorg.config import template_dir
from sportorg.core import event
from sportorg.core.app import App
from sportorg.language import _
from sportorg.lib.template.template import get_text_from_file

logging.config.dictConfig(config.LOG_CONFIG)


class MainWindow(QMainWindow, App):

    def __init__(self, argv=None):
        super().__init__()
        try:
            self.file = argv[1]
        except IndexError:
            self.file = None
        self.conf = configparser.ConfigParser()
        GlobalAccess().set_main_window(self)
        backup.init()

    def show_window(self):
        self.conf_read()
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_tab()
        self._setup_statusbar()
        self._setup_system_tray_icon()
        self.show()
        if self.file:
            self.open_file(self.file)
        if Configuration.get('autoconnect'):
            self.sportident_connect()
        event.add_event('finish', result_generation.add_result)

    def close(self):
        self.conf['geometry'] = {
            'x': self.x() + 8,
            'y': self.y() + 30,
            'width': self.width(),
            'height': self.height(),
        }
        self.conf['configuration'] = Configuration.get_all()
        self.conf_write()

        """
        :event: close
        """
        event.event('close')

    def closeEvent(self, _event):
        self.close()
        _event.accept()

    def conf_read(self):
        self.conf.read(config.CONFIG_INI)

    def conf_write(self):
        with open(config.CONFIG_INI, 'w') as configfile:
            self.conf.write(configfile)

    def _setup_ui(self):
        if self.conf.has_section(config.ConfigFile.CONFIGURATION):
            for option in self.conf.options(config.ConfigFile.CONFIGURATION):
                Configuration.set_parse(
                    option, self.conf.get(config.ConfigFile.CONFIGURATION, option, fallback=Configuration.get(option)))

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
        layout = QtWidgets.QVBoxLayout()
        toolbar = self.addToolBar(_('Toolbar'))

        for tb in toolbar_list():
            tb_action = QtWidgets.QAction(QtGui.QIcon(tb[0]), tb[1], self)
            tb_action.triggered.connect(tb[2])
            toolbar.addAction(tb_action)

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
        main_title = '{} v{}'.format(_(config.NAME), config.VERSION)
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
                logging.exception(e)
            # remove data
            if update_data:
                races[0] = Race()
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
                logging.exception(e)
        else:
            self.save_file_as()

    def open_file(self, file_name=None):
        if file_name:
            self.set_title(file_name)
            try:
                super().open_file(file_name)
            except Exception as e:
                logging.exception(e)
                QMessageBox.question(None,
                                     _('Error'),
                                     _('Cannot read file, format unknown') + ': ' + file_name)
            self.init_model()

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
            logging.error("{} {}".format(index, _('Tab not exists')))

    @staticmethod
    def get_configuration():
        return Configuration

    def settings_dialog(self):
        try:
            SettingsDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    def filter_dialog(self):
        try:
            table = GlobalAccess().get_current_table()
            ex = DialogFilter(table)
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    def report_dialog(self):
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

            person = obj.results[index].person

            if not person or not person.group:
                mes = QMessageBox()
                mes.setText(_('No results to print'))
                mes.exec()
                return

            template_path = template_dir('split_printout.html')
            spl = GroupSplits(person.group)
            template = get_text_from_file(template_path, **spl.get_json(person))

            print_html(obj.get_setting('split_printer'), template)
        except Exception as e:
            logging.exception(str(e))

    def event_settings_dialog(self):
        try:
            ex = EventPropertiesDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    def start_preparation_dialog(self):
        try:
            StartPreparationDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    def print_settings_dialog(self):
        try:
            PrintPropertiesDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    def number_change_dialog(self):
        try:
            obj = NumberChangeDialog()
            obj.exec()
        except Exception as e:
            logging.exception(str(e))

    def guess_courses(self):
        try:
            guess_courses_for_groups()
        except Exception as e:
            logging.exception(str(e))

    def guess_corridors(self):
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

    def create_start_protocol_dialog(self):
        try:
            ex = StartReportDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    def create_chess_dialog(self):
        try:
            ex = StartChessDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    def create_object(self):
        GlobalAccess().add_object()

    def delete_object(self):
        try:
            GlobalAccess().delete_object()
        except Exception as e:
            logging.exception(str(e))

    def init_model(self):
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

        except Exception as e:
            logging.exception(str(e))

    def refresh(self):
        logging.debug('refreshing interface')
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
        except Exception as e:
            logging.exception(str(e))

    def sportident_settings_dialog(self):
        try:
            SportidentPropertiesDialog().exec()
        except Exception as e:
            logging.exception(e)

    def sportident_connect(self):
        try:
            sportident.start_reader()
        except Exception as e:
            logging.exception(e)

    def import_wo_csv(self):
        file_name = get_open_file_name(_('Open CSV Winorient file'), _("CSV Winorient (*.csv)"))
        if file_name is not '':
            try:
                winorient.import_csv(file_name)
            except Exception as e:
                logging.exception(e)
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
                logging.exception(e)
            self.init_model()

    def export_wo_wdb(self):
        file_name = get_save_file_name(_('Save As WDB file'), _("WDB file (*.wdb)"),
                                       'sportorg_export_' + str(time.strftime("%Y%m%d")))
        if file_name is not '':
            try:
                winorient.export_wo_wdb(file_name)
            except Exception as e:
                logging.exception(e)

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