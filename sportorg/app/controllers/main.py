import time

import sys
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow

from sportorg.app.controllers.dialogs.entry_filter import DialogFilter
from sportorg.app.controllers.dialogs.event_properties import EventPropertiesDialog
from sportorg.app.controllers.dialogs.report_dialog import ReportDialog
from sportorg.app.controllers.global_access import GlobalAccess
from sportorg.app.controllers.tabs import start_preparation, groups, teams, race_results, courses

import configparser

from sportorg import config
from sportorg.app.models.memory import Race, event
from sportorg.app.models.memory_model import PersonMemoryModel, ResultMemoryModel, GroupMemoryModel, CourseMemoryModel, \
    TeamMemoryModel
from sportorg.app.plugins.winorient.wdb import WinOrientBinary
from sportorg.language import _


from sportorg.app.plugins.winorient import winorient
from sportorg.app.plugins.ocad import ocad
from sportorg.app.plugins.backup import backup
import logging

from sportorg.app.plugins.sportident import card_reader
from sportorg.core import plugin
from sportorg.core import event

logging.basicConfig(**config.LOG_CONFIG, level=logging.DEBUG if config.DEBUG else logging.WARNING)


class MainWindow(QMainWindow):

    def __init__(self, argv=None):
        super().__init__()
        try:
            self.file = argv[1]
        except IndexError:
            self.file = None
        self.conf = configparser.ConfigParser()
        self.reader = None
        GlobalAccess().set_main_window(self)

    def show_window(self):
        plugin.run_plugins()
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_tab()
        self.setup_statusbar()
        self.show()

    def close(self):
        print('exit', self.geometry())

    def closeEvent(self, e):
        self.close()
        e.accept()

    def conf_read(self):
        self.conf.read(config.CONFIG_INI)

    def conf_write(self):
        with open(config.CONFIG_INI, 'w') as configfile:
            self.conf.write(configfile)

    def setup_ui(self):
        self.setMinimumSize(QtCore.QSize(480, 320))
        self.setGeometry(480, 320, 480, 320)
        self.setWindowIcon(QtGui.QIcon(config.ICON))
        self.setWindowTitle(_(config.NAME))
        self.resize(880, 474)
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
        self.action_csv__winorient = QtWidgets.QAction(self)
        self.action_wdb__winorient = QtWidgets.QAction(self)
        self.action_iof__xml_v3 = QtWidgets.QAction(self)
        self.action_cvs = QtWidgets.QAction(self)
        self.action_ocad_txt_v8 = QtWidgets.QAction(self)
        self.action_help = QtWidgets.QAction(self)
        self.action_about_us = QtWidgets.QAction(self)
        self.action_report = QtWidgets.QAction(self)
        self.action_filter = QtWidgets.QAction(self)
        self.action_new_row = QtWidgets.QAction(self)
        self.action_delete = QtWidgets.QAction(self)

        self.menu_import.addAction(self.action_cvs)
        self.menu_import.addAction(self.action_csv__winorient)
        self.menu_import.addAction(self.action_wdb__winorient)
        self.menu_import.addAction(self.action_iof__xml_v3)
        self.menu_import.addSeparator()
        self.menu_import.addAction(self.action_ocad_txt_v8)

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
        self.menu_file.addAction(self.action_export)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_quit)

        self.menu_edit.addAction(self.action_new_row)
        self.menu_edit.addAction(self.action_delete)

        self.menu_start_preparation.addAction(self.action_filter)

        self.menu_results.addAction(self.action_report)

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
        self.action_cvs.setText(_("CVS "))
        self.action_cvs.setIcon(QtGui.QIcon(config.icon_dir("csv.png")))
        self.action_csv__winorient.setText(_("CSV Winorient"))
        self.action_csv__winorient.setIcon(QtGui.QIcon(config.icon_dir("csv.png")))
        self.action_csv__winorient.triggered.connect(self.import_wo_csv)
        self.action_wdb__winorient.setText(_("WDB Winorient"))
        self.action_wdb__winorient.triggered.connect(self.import_wo_wdb)
        self.action_iof__xml_v3.setText(_("IOF XML v3"))
        self.action_ocad_txt_v8.setText(_("Ocad txt v8"))
        self.action_ocad_txt_v8.triggered.connect(self.import_ocad_txt_v8)

        menu_file_import = event.event('menu_file_import')
        """
        :event: menu_file_import [[name, func],...]
        """
        for menu_import in menu_file_import:
            action_import = QtWidgets.QAction(self)
            self.menu_import.addAction(action_import)
            action_import.setText(menu_import[0])
            action_import.triggered.connect(menu_import[1])

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

        self.menu_race.setTitle(_("Race"))

        self.menu_results.setTitle(_("Results"))

        self.menu_tools.setTitle(_("Tools"))

        self.menu_service.setTitle(_("Service"))

        self.menu_options.setTitle(_("Options"))

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

        si = QtWidgets.QAction(QtGui.QIcon(config.icon_dir("sportident.png")), _("SPORTident readout"), self)
        si.triggered.connect(self.sportident)
        self.toolbar.addAction(si)

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

    def backup(self, func, mode='wb'):
        with open(self.file, mode) as file:
            func(file)

    def create_file(self):

        # TODO: save changes in current file

        file_name = QtWidgets.QFileDialog.getSaveFileName(self,'Create SportOrg file',
                                            '/' + str(time.strftime("%Y%m%d")), "SportOrg file (*.sportorg)")[0]
        if file_name is not '':
            self.setWindowTitle(file_name)
            self.file = file_name

        # remove data
        event[0] = Race()
        self.refresh()

    def save_file_as(self):
        self.create_file()
        if self.file is not None:
            self.backup(backup.dump)

    def save_file(self):
        if self.file is not None:
            self.backup(backup.dump)
        else:
            self.save_file_as()

    def open_file(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open SportOrg file',
                                                          '/',
                                                          "SportOrg file (*.sportorg)")[0]
        if file_name is not '':
            self.setWindowTitle(file_name)
            self.file = file_name
            try:
                self.backup(backup.load, 'rb')
            except:
                traceback.print_exc()
            self.init_model()

    def import_wo_csv(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open CSV Winorient file',
                                            '', "CSV Winorient (*.csv)")[0]
        if file_name is not '':
            winorient.import_csv(file_name)
            self.init_model()

    def import_wo_wdb(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open WDB Winorient file',
                                            '', "WDB Winorient (*.wdb)")[0]
        if file_name is not '':
            try:
                wb = WinOrientBinary(file=file_name)
                # wb.run()
                wb.create_objects()
                self.init_model()
            except:
                print(sys.exc_info())
                traceback.print_exc()

    def import_ocad_txt_v8(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open Ocad txt v8 file',
                                                          '', "Ocad classes v8 (*.txt)")[0]
        if file_name is not '':
            try:
                ocad.import_txt_v8(file_name)
            except:
                traceback.print_exc()

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
            print(sys.exc_info())
            traceback.print_exc()

    def create_object(self):
        GlobalAccess().add_object()

    def delete_object(self):
        GlobalAccess().delete_object()

    def init_model(self):
        try:
            table = GlobalAccess().get_person_table()
            table.model().setSourceModel(PersonMemoryModel())
            table = GlobalAccess().get_result_table()
            table.model().setSourceModel(ResultMemoryModel())
            table = GlobalAccess().get_group_table()
            table.model().setSourceModel(GroupMemoryModel())
            table = GlobalAccess().get_course_table()
            table.model().setSourceModel(CourseMemoryModel())
            table = GlobalAccess().get_organization_table()
            table.model().setSourceModel(TeamMemoryModel())

        except:
            traceback.print_exc()

    def refresh(self):
        try:
            table = GlobalAccess().get_person_table()
            table.model().sourceModel().init_cache()
            table = GlobalAccess().get_result_table()
            table.model().sourceModel().init_cache()
            table = GlobalAccess().get_group_table()
            table.model().sourceModel().init_cache()
            table = GlobalAccess().get_course_table()
            table.model().sourceModel().init_cache()
            table = GlobalAccess().get_organization_table()
            table.model().sourceModel().init_cache()
        except:
            traceback.print_exc()

    def sportident(self):
        if self.reader is None:
            self.reader = card_reader.read()
            if self.reader is not None:
                self.statusbar.showMessage(_('Open port ' + self.reader.port), 5000)
                f_id = self.reader.append_reader(lambda data: print('from main.py', data))
                # self.reader.delete_func(f_id)
            else:
                self.statusbar.showMessage(_('Port not open'), 5000)
        elif not self.reader.reading:
            self.reader = None
            self.sportident()
        else:
            card_reader.stop(self.reader)
            if not self.reader.reading:
                port = self.reader.port
                self.reader = None
                self.statusbar.showMessage(_('Close port ' + port), 5000)
