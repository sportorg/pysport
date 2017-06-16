import time

import sys
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow

from sportorg.app.controllers.dialogs.entry_filter import DialogFilter
from sportorg.app.controllers.tabs import start_preparation, groups, teams, race_results, courses

import configparser

import config
from sportorg.app.models.memory_model import PersonMemoryModel, ResultMemoryModel, GroupMemoryModel, CourseMemoryModel, \
    TeamMemoryModel
from sportorg.app.models.table_model import PersonTableModel, ResultTableModel
from sportorg.app.plugins.winorient.wdb import WinOrientBinary
from sportorg.language import _
from sportorg.app.models import model


from sportorg.app.plugins.winorient import winorient
from sportorg.app.plugins.ocad import ocad
import logging

from sportorg.lib.winorient.wdb import parse_wdb

logging.basicConfig(**config.LOG_CONFIG, level=logging.DEBUG if config.DEBUG else logging.WARNING)


class MainWindow(object):
    def __init__(self, argv=None):
        try:
            self.file = argv[1]
        except IndexError:
            self.file = None
        self.mainwindow = QMainWindow()
        self.conf = configparser.ConfigParser()

    def show(self):
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_tab()
        self.setup_statusbar()
        self.mainwindow.show()

    def setup_ui(self):
        self.mainwindow.setMinimumSize(QtCore.QSize(480, 320))
        self.mainwindow.setGeometry(480, 320, 480, 320)
        self.mainwindow.setWindowIcon(QtGui.QIcon(config.ICON))
        self.mainwindow.setWindowTitle(_(config.NAME))
        self.mainwindow.resize(880, 474)
        self.mainwindow.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.mainwindow.setDockNestingEnabled(False)
        self.mainwindow.setDockOptions(QtWidgets.QMainWindow.AllowTabbedDocks
                                       | QtWidgets.QMainWindow.AnimatedDocks
                                       | QtWidgets.QMainWindow.ForceTabbedDocks)

    def setup_menu(self):
        self.menubar = QtWidgets.QMenuBar(self.mainwindow)
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
        self.mainwindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(self.mainwindow)
        self.mainwindow.setStatusBar(self.statusbar)
        self.action_save = QtWidgets.QAction(self.mainwindow)
        self.action_open = QtWidgets.QAction(self.mainwindow)
        self.action_quit = QtWidgets.QAction(self.mainwindow)
        self.action_new = QtWidgets.QAction(self.mainwindow)
        self.action_new__race = QtWidgets.QAction(self.mainwindow)
        self.action_save_as = QtWidgets.QAction(self.mainwindow)
        self.action_open__resent = QtWidgets.QAction(self.mainwindow)
        self.action_settings = QtWidgets.QAction(self.mainwindow)
        self.action_event__settings = QtWidgets.QAction(self.mainwindow)
        self.action_export = QtWidgets.QAction(self.mainwindow)
        self.action_csv__winorient = QtWidgets.QAction(self.mainwindow)
        self.action_wdb__winorient = QtWidgets.QAction(self.mainwindow)
        self.action_iof__xml_v3 = QtWidgets.QAction(self.mainwindow)
        self.action_cvs = QtWidgets.QAction(self.mainwindow)
        self.action_ocad_txt_v8 = QtWidgets.QAction(self.mainwindow)
        self.action_help = QtWidgets.QAction(self.mainwindow)
        self.action_about_us = QtWidgets.QAction(self.mainwindow)
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
        self.action_filter = QtWidgets.QAction(self.mainwindow)
        self.menu_start_preparation.addAction(self.action_filter)
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
        self.action_export.setText(_("Export"))
        self.action_quit.setText(_("Exit"))
        self.action_filter.setText(_("Filter"))
        self.action_filter.triggered.connect(self.filter_dialog)
        self.action_filter.setShortcut("F2")

        self.menu_edit.setTitle(_("Edit"))

        self.menu_start_preparation.setTitle(_("Start preparation"))

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
        self.toolbar = self.mainwindow.addToolBar("File")

        new = QtWidgets.QAction(QtGui.QIcon(config.icon_dir("file.png")), "new", self.mainwindow)
        new.triggered.connect(self.create_file)
        self.toolbar.addAction(new)

        open = QtWidgets.QAction(QtGui.QIcon(config.icon_dir("folder.png")), "open", self.mainwindow)
        open.triggered.connect(self.open_file)
        self.toolbar.addAction(open)
        save = QtWidgets.QAction(QtGui.QIcon(config.icon_dir("save.png")), "save", self.mainwindow)
        self.toolbar.addAction(save)

        self.mainwindow.setLayout(layout)

    def setup_statusbar(self):
        self.statusbar = QtWidgets.QStatusBar()
        self.mainwindow.setStatusBar(self.statusbar)
        self.statusbar.showMessage(_("it works!"), 5000)

    def setup_tab(self):
        self.centralwidget = QtWidgets.QWidget(self.mainwindow)
        layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.tabwidget = QtWidgets.QTabWidget(self.centralwidget)
        layout.addWidget(self.tabwidget)
        self.mainwindow.setCentralWidget(self.centralwidget)

        self.tabwidget.addTab(start_preparation.Widget(), _("Start Preparation"))
        self.tabwidget.addTab(race_results.Widget(), _("Race Results"))
        self.tabwidget.addTab(groups.Widget(), _("Groups"))
        self.tabwidget.addTab(courses.Widget(), _("Courses"))
        self.tabwidget.addTab(teams.Widget(), _("Teams"))

    def create_file(self):
        file_name = QtWidgets.QFileDialog.getSaveFileName(self.mainwindow,'Create SportOrg file',
                                            '/' + str(time.strftime("%Y%m%d")), "SportOrg file (*.sportorg)")[0]
        if file_name is not '':
            self.mainwindow.setWindowTitle(file_name)
            self.file = file_name

    def save_file_as(self):
        file_name = QtWidgets.QFileDialog.getSaveFileName(self.mainwindow,'Save As SportOrg file',
                                            '/' + str(time.strftime("%Y%m%d")), "SportOrg file (*.sportorg)")[0]
        if file_name is not '':
            self.mainwindow.setWindowTitle(file_name)
            self.file = file_name

    def save_file(self):
        pass

    def open_file(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self.mainwindow, 'Open SportOrg file',
                                                          '/',
                                                          "SportOrg file (*.sportorg)")[0]
        if file_name is not '':
            self.mainwindow.setWindowTitle(file_name)
            self.file = file_name

    def import_wo_csv(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self.mainwindow, 'Open CSV Winorient file',
                                            '', "CSV Winorient (*.csv)")[0]
        if file_name is not '':
            winorient.import_csv(file_name)
            # self.tabwidget.update(start_preparation.Widget())
            # try:
            #     table = self.tabwidget.findChild(QtWidgets.QTableView, 'EntryTable')
            #     table.model().setSourceModel(PersonTableModel())
            # except:
            #     print(sys.exc_info())

    def import_wo_wdb(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self.mainwindow, 'Open WDB Winorient file',
                                            '', "WDB Winorient (*.wdb)")[0]
        if file_name is not '':
            try:
                wb = WinOrientBinary(file=file_name)
                # wb.run()
                wb.create_objects()
                table = self.tabwidget.findChild(QtWidgets.QTableView, 'EntryTable')
                table.model().setSourceModel(PersonMemoryModel())
                table = self.tabwidget.findChild(QtWidgets.QTableView, 'ResultTable')
                table.model().setSourceModel(ResultMemoryModel())
                table = self.tabwidget.findChild(QtWidgets.QTableView, 'GroupTable')
                table.model().setSourceModel(GroupMemoryModel())
                table = self.tabwidget.findChild(QtWidgets.QTableView, 'CourseTable')
                table.model().setSourceModel(CourseMemoryModel())
                table = self.tabwidget.findChild(QtWidgets.QTableView, 'TeamTable')
                table.model().setSourceModel(TeamMemoryModel())
            except:
                print(sys.exc_info())
                traceback.print_exc()

    def import_ocad_txt_v8(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self.mainwindow, 'Open Ocad txt v8 file',
                                                          '', "Ocad classes v8 (*.txt)")[0]
        if file_name is not '':
            ocad.import_txt_v8(file_name)

    def filter_dialog(self):
        try:
            table = self.tabwidget.findChild(QtWidgets.QTableView, 'EntryTable')
            ex = DialogFilter(table)
            ex.exec()
        except:
            print(sys.exc_info())
            traceback.print_exc()
