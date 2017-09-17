import configparser
import logging
import sys
import time
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow

from sportorg import config
from sportorg.app.controllers.dialogs.entry_filter import DialogFilter
from sportorg.app.controllers.dialogs.event_properties import EventPropertiesDialog
from sportorg.app.controllers.dialogs.number_change import NumberChangeDialog
from sportorg.app.controllers.dialogs.report_dialog import ReportDialog
from sportorg.app.controllers.dialogs.sportident_properties import SportidentPropertiesDialog
from sportorg.app.controllers.dialogs.start_preparation import StartPreparationDialog, guess_courses_for_groups
from sportorg.app.controllers.global_access import GlobalAccess
from sportorg.app.controllers.tabs import start_preparation, groups, teams, race_results, courses
from sportorg.app.models.memory import Race, event as e
from sportorg.app.models import result_generation
from sportorg.app.models.memory_model import PersonMemoryModel, ResultMemoryModel, GroupMemoryModel, CourseMemoryModel, \
    TeamMemoryModel
from sportorg.core import event
from sportorg.core import plugin, app
from sportorg.language import _

logging.basicConfig(**config.LOG_CONFIG, level=logging.DEBUG if config.DEBUG else logging.WARNING)


class MainWindow(QMainWindow, app.App):

    def __init__(self, argv=None):
        super().__init__()
        try:
            self.file = argv[1]
        except IndexError:
            self.file = None
        self.conf = configparser.ConfigParser()
        GlobalAccess().set_main_window(self)

    def show_window(self):
        plugin.run_plugins()
        event.event('mainwindow', self)
        event.add_event('init_model', (self, 'init_model'))
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

    def setup_menu(self):
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 880, 21))

        self.menu_file = QtWidgets.QMenu(self.menubar)
        self.menu_import = QtWidgets.QMenu(self.menu_file)
        self.menu_export = QtWidgets.QMenu(self.menu_file)
        self.menu_start_preparation = QtWidgets.QMenu(self.menubar)
        self.menu_race = QtWidgets.QMenu(self.menubar)
        self.menu_help = QtWidgets.QMenu(self.menubar)
        self.menu_results = QtWidgets.QMenu(self.menubar)
        self.menu_edit = QtWidgets.QMenu(self.menubar)
        self.menu_tools = QtWidgets.QMenu(self.menubar)
        self.menu_service = QtWidgets.QMenu(self.menubar)
        self.menu_options = QtWidgets.QMenu(self.menubar)

        self.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.action_save = QtWidgets.QAction(self)
        self.action_open = QtWidgets.QAction(self)
        self.action_quit = QtWidgets.QAction(self)
        self.action_new = QtWidgets.QAction(self)
        self.action_new__race = QtWidgets.QAction(self)
        self.action_save_as = QtWidgets.QAction(self)
        self.action_open__resent = QtWidgets.QAction(self)
        self.action_settings = QtWidgets.QAction(self)
        self.action_event__settings = QtWidgets.QAction(self)
        self.action_export = QtWidgets.QAction(self)
        self.action_help = QtWidgets.QAction(self)
        self.action_about_us = QtWidgets.QAction(self)
        self.action_report = QtWidgets.QAction(self)
        self.action_filter = QtWidgets.QAction(self)
        self.action_new_row = QtWidgets.QAction(self)
        self.action_delete = QtWidgets.QAction(self)
        self.action_start_preparation = QtWidgets.QAction(self)
        self.action_number_change = QtWidgets.QAction(self)
        self.action_guess_courses = QtWidgets.QAction(self)
        self.action_sportident_settings = QtWidgets.QAction(self)

        self.menu_import.addSeparator()

        self.menu_file.addAction(self.action_new)
        self.menu_file.addAction(self.action_new__race)
        self.menu_file.addAction(self.action_save)
        self.menu_file.addAction(self.action_save_as)
        self.menu_file.addAction(self.action_open)
        self.menu_file.addAction(self.action_open__resent)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_settings)
        self.menu_file.addAction(self.action_event__settings)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.menu_import.menuAction())
        self.menu_file.addAction(self.menu_export.menuAction())
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_quit)

        self.menu_edit.addAction(self.action_new_row)
        self.menu_edit.addAction(self.action_delete)

        self.menu_start_preparation.addAction(self.action_filter)
        self.menu_start_preparation.addAction(self.action_start_preparation)
        self.menu_start_preparation.addAction(self.action_number_change)
        self.menu_start_preparation.addAction(self.action_guess_courses)

        self.menu_results.addAction(self.action_report)

        self.menu_options.addAction(self.action_sportident_settings)

        self.menu_help.addAction(self.action_help)
        self.menu_help.addAction(self.action_about_us)

        self.menubar.addAction(self.menu_file.menuAction())
        self.menubar.addAction(self.menu_edit.menuAction())
        self.menubar.addAction(self.menu_start_preparation.menuAction())
        self.menubar.addAction(self.menu_race.menuAction())
        self.menubar.addAction(self.menu_results.menuAction())
        self.menubar.addAction(self.menu_tools.menuAction())
        self.menubar.addAction(self.menu_service.menuAction())
        self.menubar.addAction(self.menu_options.menuAction())
        self.menubar.addAction(self.menu_help.menuAction())

        self.menu_file.setTitle(_("File"))
        # method connect of PyQt5.QtCore.pyqtBoundSignal object
        self.action_new.setText(_("New"))
        self.action_new.setIcon(QtGui.QIcon(config.icon_dir("file.png")))
        self.action_new.triggered.connect(self.create_file)
        self.action_save.setText(_("Save"))
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.setIcon(QtGui.QIcon(config.icon_dir("save.png")))
        self.action_save.triggered.connect(self.save_file)
        self.action_open.setText(_("Open"))
        self.action_open.setShortcut("Ctrl+O")
        self.action_open.triggered.connect(self.open_file)
        self.action_open.setIcon(QtGui.QIcon(config.icon_dir("folder.png")))
        self.action_new.setShortcut("Ctrl+N")
        self.action_new__race.setText(_("New Race"))
        self.action_save_as.setText(_("Save As"))
        self.action_save_as.setShortcut("Ctrl+Shift+S")
        self.action_save_as.setIcon(QtGui.QIcon(config.icon_dir("save.png")))
        self.action_save_as.triggered.connect(self.save_file_as)
        self.action_open__resent.setText(_("Open Recent"))
        self.action_settings.setText(_("Settings"))
        self.action_event__settings.setText(_("Event Settings"))
        self.action_event__settings.triggered.connect(self.event_settings_dialog)
        self.menu_import.setTitle(_("Import"))

        menu_file_import = event.event('menu_file_import')
        """
        :event: menu_file_import [[name, func, icon?],...]
        """
        if menu_file_import is not None:
            for menu_import in menu_file_import:
                action_import = QtWidgets.QAction(self)
                self.menu_import.addAction(action_import)
                action_import.setText(menu_import[0])
                action_import.triggered.connect(menu_import[1])
                if len(menu_import) == 3:
                    action_import.setIcon(QtGui.QIcon(menu_import[2]))

        self.menu_export.setTitle(_("Export"))
        menu_file_export = event.event('menu_file_export')
        """
        :event: menu_file_export [[name, func, icon?],...]
        """
        if menu_file_export is not None:
            for menu_export in menu_file_export:
                action_export = QtWidgets.QAction(self)
                self.menu_export.addAction(action_export)
                action_export.setText(menu_export[0])
                action_export.triggered.connect(menu_export[1])
                if len(menu_export) == 3:
                    action_export.setIcon(QtGui.QIcon(menu_export[2]))

        self.action_export.setText(_("Export"))
        self.action_quit.setText(_("Exit"))
        self.action_filter.setText(_("Filter"))
        self.action_filter.triggered.connect(self.filter_dialog)
        self.action_filter.setShortcut("F2")
        self.action_report.setText(_("Create report"))
        self.action_report.triggered.connect(self.report_dialog)
        self.action_report.setShortcut("Ctrl+P")

        self.action_new_row.setText(_("Add object"))
        self.action_new_row.triggered.connect(self.create_object)
        self.action_delete.setText(_("Delete"))
        self.action_delete.setShortcut("Del")
        self.action_delete.triggered.connect(self.delete_object)

        self.menu_edit.setTitle(_("Edit"))

        self.menu_start_preparation.setTitle(_("Start Preparation"))
        self.action_start_preparation.setText(_("Start Preparation"))
        self.action_start_preparation.triggered.connect(self.start_preparation)
        self.action_number_change.setText(_("Number Change"))
        self.action_number_change.triggered.connect(self.number_change)
        self.action_guess_courses.setText(_("Guess courses"))
        self.action_guess_courses.triggered.connect(self.guess_courses)

        self.menu_race.setTitle(_("Race"))

        self.menu_results.setTitle(_("Results"))

        self.menu_tools.setTitle(_("Tools"))

        self.menu_service.setTitle(_("Service"))

        self.menu_options.setTitle(_("Options"))
        self.action_sportident_settings.setText(_('SPORTident settings'))
        self.action_sportident_settings.triggered.connect(self.sportident_settings)

        self.menu_help.setTitle(_("Help"))
        self.action_help.setText(_("Help"))
        self.action_about_us.setText(_("About"))

    def setup_toolbar(self):
        layout = QtWidgets.QVBoxLayout()
        self.toolbar = self.addToolBar("File")

        new = QtWidgets.QAction(QtGui.QIcon(config.icon_dir("file.png")), _("New"), self)
        new.triggered.connect(self.create_file)
        self.toolbar.addAction(new)

        open = QtWidgets.QAction(QtGui.QIcon(config.icon_dir("folder.png")), _("Open"), self)
        open.triggered.connect(self.open_file)
        self.toolbar.addAction(open)
        save = QtWidgets.QAction(QtGui.QIcon(config.icon_dir("save.png")), _("Save"), self)
        save.triggered.connect(self.save_file)
        self.toolbar.addAction(save)

        toolbar_event = event.event('toolbar')
        """
        :event: toolbar [[icon, title, func],...]
        """
        if toolbar_event is not None:
            for tb in toolbar_event:
                tb_action = QtWidgets.QAction(QtGui.QIcon(tb[0]), tb[1], self)
                tb_action.triggered.connect(tb[2])
                self.toolbar.addAction(tb_action)

        self.setLayout(layout)

    def setup_statusbar(self):
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage(_("it works!"), 5000)
        event.event('statusbar', self.statusbar)

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
            super().create_file(file_name)
            # remove data
            if update_data:
                e[0] = Race()
            self.refresh()

    def save_file_as(self):
        self.create_file(None, False)
        if self.file is not None:
            self.save_file()

    def save_file(self):
        if self.file is not None:
            super().save_file()
        else:
            self.save_file_as()

    def open_file(self, file_name=None):
        file_name = QtWidgets.QFileDialog.getOpenFileName(None, 'Open SportOrg file',
                                                          '/',
                                                          "SportOrg file (*.sportorg)")[0]
        if file_name is not '':
            self.setWindowTitle(file_name)
            super().open_file(file_name)
            self.init_model()

    def filter_dialog(self):
        try:
            table = GlobalAccess().get_current_table()
            ex = DialogFilter(table)
            ex.exec()
        except:
            print(sys.exc_info())
            traceback.print_exc()

    def report_dialog(self):
        try:
            ex = ReportDialog()
            ex.exec()
        except:
            print(sys.exc_info())
            traceback.print_exc()

    def event_settings_dialog(self):
        try:
            ex = EventPropertiesDialog()
            ex.exec()
        except:
            traceback.print_exc()

    def start_preparation(self):
        try:
            StartPreparationDialog().exec()
        except:
            traceback.print_exc()

    def sportident_settings(self):
        try:
            SportidentPropertiesDialog().exec()
        except:
            traceback.print_exc()

    def number_change(self):
        try:
            obj = NumberChangeDialog()
            obj.exec()
        except:
            traceback.print_exc()

    def guess_courses(self):
        try:
            guess_courses_for_groups()
        except:
            traceback.print_exc()

    def create_object(self):
        GlobalAccess().add_object()

    def delete_object(self):
        try:
            GlobalAccess().delete_object()
        except:
            traceback.print_exc()

    def init_model(self):
        try:
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

        except:
            traceback.print_exc()

    def refresh(self):

        print("refreshing interface")
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

            event.event('refresh_window')
        except:
            traceback.print_exc()
