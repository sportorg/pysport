import configparser
import logging.config
import time

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QTableView, QMessageBox

from sportorg import config
from sportorg.app.controllers.dialogs.entry_filter import DialogFilter
from sportorg.app.controllers.dialogs.event_properties import EventPropertiesDialog
from sportorg.app.controllers.dialogs.number_change import NumberChangeDialog
from sportorg.app.controllers.dialogs.print_properties import PrintPropertiesDialog
from sportorg.app.controllers.dialogs.report_dialog import ReportDialog
from sportorg.app.controllers.dialogs.start_chess_dialog import StartChessDialog
from sportorg.app.controllers.dialogs.start_preparation import StartPreparationDialog
from sportorg.app.controllers.dialogs.start_report_dialog import StartReportDialog
from sportorg.app.controllers.global_access import GlobalAccess
from sportorg.app.controllers.menu import menu_list
from sportorg.app.controllers.tabs import start_preparation, groups, teams, race_results, courses
from sportorg.app.controllers.toolbar import toolbar_list
from sportorg.app.models.memory import Race, event as races, race
from sportorg.app.models import result_generation
from sportorg.app.models.memory_model import PersonMemoryModel, ResultMemoryModel, GroupMemoryModel, \
    CourseMemoryModel, TeamMemoryModel
from sportorg.app.models.split_calculation import GroupSplits
from sportorg.app.models.start_preparation import guess_courses_for_groups, guess_corridors_for_groups
from sportorg.app.modules.backup import backup
from sportorg.app.modules.printing.printing import print_html
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
        event.add_event('finish', result_generation.add_result)
        self.conf_read()
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_tab()
        self.setup_statusbar()
        self.show()

    def close(self):
        self.conf['geometry'] = {
            'x': self.x() + 8,
            'y': self.y() + 30,
            'width': self.width(),
            'height': self.height(),
        }
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

    def setup_ui(self):
        geometry = 'geometry'
        x = self.conf.getint('%s' % geometry, 'x', fallback=480)
        y = self.conf.getint(geometry, 'y', fallback=320)
        width = self.conf.getint(geometry, 'width', fallback=880)
        height = self.conf.getint(geometry, 'height', fallback=474)

        self.setMinimumSize(QtCore.QSize(480, 320))
        self.setGeometry(x, y, 480, 320)
        self.setWindowIcon(QtGui.QIcon(config.ICON))
        self.setWindowTitle(_(config.NAME))
        self.resize(width, height)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setDockNestingEnabled(False)
        self.setDockOptions(QtWidgets.QMainWindow.AllowTabbedDocks
                                       | QtWidgets.QMainWindow.AnimatedDocks
                                       | QtWidgets.QMainWindow.ForceTabbedDocks)

    def create_menu(self, parent, actions_list):
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
                self.create_menu(menu, action_item['actions'])
                parent.addAction(menu.menuAction())

    def setup_menu(self):
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 880, 21))
        self.setMenuBar(self.menubar)

        self.create_menu(self.menubar, menu_list())

    def setup_toolbar(self):
        layout = QtWidgets.QVBoxLayout()
        toolbar = self.addToolBar("File")

        for tb in toolbar_list():
            tb_action = QtWidgets.QAction(QtGui.QIcon(tb[0]), tb[1], self)
            tb_action.triggered.connect(tb[2])
            toolbar.addAction(tb_action)

        self.setLayout(layout)

    def setup_statusbar(self):
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage(_("it works!"), 5000)

    def setup_tab(self):
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

    def create_file(self, file_name=None, update_data=True):

        # TODO: save changes in current file

        file_name = QtWidgets.QFileDialog.getSaveFileName(None, 'Create SportOrg file',
                                            '/' + str(time.strftime("%Y%m%d")), "SportOrg file (*.sportorg)")[0]
        if file_name is not '':
            self.setWindowTitle(file_name)
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
        file_name = QtWidgets.QFileDialog.getOpenFileName(None, 'Open SportOrg file',
                                                          '/',
                                                          "SportOrg file (*.sportorg)")[0]
        if file_name is not '':
            self.setWindowTitle(file_name)
            try:
                super().open_file(file_name)
            except Exception as e:
                logging.exception(e)
            self.init_model()

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

    def start_preparation(self):
        try:
            StartPreparationDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    def print_settings(self):
        try:
            PrintPropertiesDialog().exec()
        except Exception as e:
            logging.exception(str(e))

    def number_change(self):
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
        except Exception as e:
            logging.exception(str(e))

    def create_start_protocol(self):
        try:
            ex = StartReportDialog()
            ex.exec()
        except Exception as e:
            logging.exception(str(e))

    def create_chess(self):
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
