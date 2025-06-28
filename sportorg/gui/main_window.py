import ast
import logging
import os
import time
from os import remove
from os.path import exists
from queue import Queue

import psutil
from psutil import Process

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QMainWindow, QMessageBox
except ModuleNotFoundError:
    from PySide2 import QtCore, QtGui, QtWidgets
    from PySide2.QtCore import QTimer
    from PySide2.QtGui import QActionEvent
    from PySide2.QtWidgets import QAction, QMainWindow, QMessageBox

from sportorg import config
from sportorg.gui.dialogs.course_edit import CourseEditDialog
from sportorg.gui.dialogs.file_dialog import get_save_file_name
from sportorg.gui.dialogs.group_edit import GroupEditDialog
from sportorg.gui.dialogs.organization_edit import OrganizationEditDialog
from sportorg.gui.dialogs.person_edit import PersonEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.menu import Factory, menu_list
from sportorg.gui.tabs import courses, groups, log, organizations, persons, results
from sportorg.gui.tabs.memory_model import (
    CourseMemoryModel,
    GroupMemoryModel,
    OrganizationMemoryModel,
    PersonMemoryModel,
    ResultMemoryModel,
)
from sportorg.gui.toolbar import toolbar_list
from sportorg.gui.utils.custom_controls import messageBoxQuestion
from sportorg.language import translate
from sportorg.models.constant import RentCards
from sportorg.models.memory import (
    NotEmptyException,
    Race,
    RaceType,
    get_current_race_index,
    new_event,
    race,
    races,
    set_current_race_index,
)
from sportorg.models.result.result_tools import recalculate_results
from sportorg.models.result.split_calculation import GroupSplits
from sportorg.modules.backup.file import File
from sportorg.modules.configs.configs import Config as Configuration
from sportorg.modules.configs.configs import ConfigFile
from sportorg.modules.live.live import live_client
from sportorg.modules.printing.model import (
    NoPrinterSelectedException,
    NoResultToPrintException,
    split_printout,
    split_printout_close,
)
from sportorg.modules.rfid_impinj.rfid_impinj import ImpinjClient
from sportorg.modules.sfr.sfrreader import SFRReaderClient
from sportorg.modules.sound import Sound
from sportorg.modules.sportident.result_generation import ResultSportidentGeneration
from sportorg.modules.sportident.sireader import SIReaderClient
from sportorg.modules.sportiduino.sportiduino import SportiduinoClient
from sportorg.modules.srpid.srpid import SrpidClient
from sportorg.modules.teamwork.packet_header import ObjectTypes
from sportorg.modules.teamwork.teamwork import Teamwork
from sportorg.modules.telegram.telegram import telegram_client


class ConsolePanelHandler(logging.Handler):
    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.setFormatter(logging.Formatter("%(asctime)-15s %(levelname)s %(message)s"))
        self.setLevel("INFO")
        self.parent = parent

    def emit(self, record):
        self.parent.logging(
            dict({"text": self.format(record), "level": record.levelno})
        )


def is_reading_active():
    return (
        SIReaderClient().is_alive()
        or SFRReaderClient().is_alive()
        or ImpinjClient().is_alive()
        or SportiduinoClient().is_alive()
        or SrpidClient().is_alive()
    )


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
        self._handler = ConsolePanelHandler(self)

        logging.root.addHandler(self._handler)

        self.last_update = time.time()
        self.relay_number_assign = False
        self.split_printer_thread = None
        self.split_printer_queue = None

    def _set_style(self):
        try:
            with open(config.style_dir("default.qss")) as s:
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
        if Configuration().configuration.get("show_toolbar"):
            self._setup_toolbar()
        self._setup_tab()
        self._setup_statusbar()
        self.show()
        self.post_show()

    sportident_status = False
    sportident_icon = {
        True: "sportident-on.png",
        False: "sportident.png",
    }

    def teamwork(self, command):
        try:
            race().update_data(command.data)
            # if 'object' in command.data and command.data['object'] in
            # ['ResultManual', 'ResultSportident', 'ResultSFR', 'ResultSportiduino' etc.]:
            if command.header.obj_type in [
                ObjectTypes.Result.value,
                ObjectTypes.ResultManual.value,
                ObjectTypes.ResultSportident.value,
                ObjectTypes.ResultSFR.value,
                ObjectTypes.ResultSportiduino.value,
                ObjectTypes.ResultSrpid.value,
                ObjectTypes.ResultRfidImpinj.value,
            ]:
                self.deleyed_res_recalculate(1000)

            self.deleyed_refresh(1000)

        except Exception as e:
            logging.error(str(e))

    teamwork_status = False
    teamwork_icon = {
        True: "network.svg",
        False: "network-off.svg",
    }

    def interval(self):
        if is_reading_active() != self.sportident_status and hasattr(self, "toolbar"):
            self.sportident_status = is_reading_active()

            self.toolbar_property["sportident"].setIcon(
                QtGui.QIcon(
                    config.icon_dir(self.sportident_icon[self.sportident_status])
                )
            )

        if Teamwork().is_alive() != self.teamwork_status:
            self.toolbar_property["teamwork"].setIcon(
                QtGui.QIcon(config.icon_dir(self.teamwork_icon[Teamwork().is_alive()]))
            )
            self.teamwork_status = Teamwork().is_alive()

        try:
            if self.get_configuration().get("autosave_interval"):
                if self.file:
                    if time.time() - self.last_update > int(
                        self.get_configuration().get("autosave_interval")
                    ):
                        self.save_file()
                        logging.info(translate("Auto save"))
                else:
                    pass
                    # logging.debug(translate('No file to auto save'))
        except Exception as e:
            logging.error(str(e))

        while not self.log_queue.empty():
            rec = self.log_queue.get()
            text = rec["text"]
            lvl = int(rec["level"])
            self.statusbar_message(text)
            if hasattr(self, "logging_tab"):
                self.logging_tab.write(text)
                if (
                    lvl >= logging.ERROR
                    and self.tabbar.tabTextColor(
                        self.tabwidget.indexOf(self.logging_tab)
                    )
                    != self.logging_tab.error_color
                ):
                    self.tabbar.setTabTextColor(
                        self.tabwidget.indexOf(self.logging_tab),
                        self.logging_tab.error_color,
                    )

    def close(self):
        self.conf_write()
        self.unlock_file(self.file)

    def close_split_printer(self):
        if self.split_printer_thread:
            split_printout_close()
            self.set_split_printer_thread(None)

        if self.split_printer_queue:
            self.split_printer_queue.close()
            self.set_split_printer_queue(None)

    def closeEvent(self, _event):
        quit_msg = translate("Save file before exit?")
        reply = messageBoxQuestion(
            self,
            translate("Question"),
            quit_msg,
            QMessageBox.Save | QMessageBox.No | QMessageBox.Cancel,
        )

        self.close_split_printer()
        if reply == QMessageBox.Save:
            self.save_file()
            self.close()
            _event.accept()
        elif reply == QMessageBox.No:
            self.close()
            _event.accept()
        else:
            _event.ignore()

    def conf_read(self):
        Configuration().read()
        if Configuration().parser.has_section(ConfigFile.PATH):
            try:
                recent_files = ast.literal_eval(
                    Configuration().parser.get(
                        ConfigFile.PATH, "recent_files", fallback="[]"
                    )
                )
                if isinstance(recent_files, list):
                    self.recent_files = recent_files
            except Exception as e:
                logging.error(str(e))

        level: str = Configuration().configuration.get("logging_level", "INFO")
        self._handler.setLevel(level)

        dirpath = Configuration().templates.get("directory")
        if dirpath:
            config.set_template_dir(dirpath)

    def conf_write(self):
        Configuration().save()

    def post_show(self):
        if self.file:
            self.open_file(self.file)
        elif Configuration().configuration.get("open_recent_file"):
            if len(self.recent_files):
                self.open_file(self.recent_files[0])

        Teamwork().set_call(self.teamwork)
        SIReaderClient().set_call(self.add_sportident_result_from_sireader)
        SportiduinoClient().set_call(self.add_sportiduino_result_from_reader)
        ImpinjClient().set_call(self.add_impinj_result_from_reader)
        SFRReaderClient().set_call(self.add_sfr_result_from_reader)
        SrpidClient().set_call(self.add_srpid_result_from_reader)

        self.service_timer = QTimer(self)
        self.service_timer.timeout.connect(self.interval)
        self.service_timer.start(1000)  # msec

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_by_timer)

        self.res_recalculate = QTimer(self)
        self.res_recalculate.timeout.connect(self.res_recalculate_by_timer)

        live_client.init()
        self._menu_disable(self.current_tab)

    def _setup_ui(self):
        geometry = ConfigFile.GEOMETRY

        geom = bytearray.fromhex(
            Configuration().parser.get(geometry, "main", fallback="01")
        )
        self.restoreGeometry(geom)

        self.setWindowIcon(QtGui.QIcon(config.ICON))
        self.set_title()

        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setDockNestingEnabled(False)
        self.setDockOptions(
            QtWidgets.QMainWindow.AllowTabbedDocks
            | QtWidgets.QMainWindow.AnimatedDocks
            | QtWidgets.QMainWindow.ForceTabbedDocks
        )

    def _create_menu(self, parent, actions_list):
        for action_item in actions_list:
            if "show" in action_item and not action_item["show"]:
                return
            if "type" in action_item:
                if action_item["type"] == "separator":
                    parent.addSeparator()
            elif "action" in action_item:
                action = QAction(self)
                action.setText(action_item["title"])
                action.triggered.connect(
                    self.menu_factory.get_action(action_item["action"])
                )
                if "shortcut" in action_item:
                    shortcuts = (
                        [action_item["shortcut"]]
                        if isinstance(action_item["shortcut"], str)
                        else action_item["shortcut"]
                    )
                    action.setShortcuts(shortcuts)
                if "icon" in action_item:
                    action.setIcon(QtGui.QIcon(action_item["icon"]))
                if "status_tip" in action_item:
                    action.setStatusTip(action_item["status_tip"])
                if "tabs" in action_item:
                    self.menu_list_for_disabled.append((action, action_item["tabs"]))
                if "property" in action_item:
                    self.menu_property[action_item["property"]] = action
                if (
                    "debug" in action_item and action_item["debug"]
                ) or "debug" not in action_item:
                    parent.addAction(action)
            else:
                menu = QtWidgets.QMenu(parent)
                menu.setTitle(action_item["title"])
                if "icon" in action_item:
                    menu.setIcon(QtGui.QIcon(action_item["icon"]))
                if "tabs" in action_item:
                    self.menu_list_for_disabled.append((menu, action_item["tabs"]))
                self._create_menu(menu, action_item["actions"])
                parent.addAction(menu.menuAction())

    def _setup_menu(self):
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 880, 21))
        self.setMenuBar(self.menubar)
        self._create_menu(self.menubar, menu_list())

    def _setup_toolbar(self):
        self.toolbar = self.addToolBar(translate("Toolbar"))
        for tb in toolbar_list():
            tb_action = QAction(QtGui.QIcon(tb[0]), tb[1], self)
            tb_action.triggered.connect(self.menu_factory.get_action(tb[2]))
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

        self.tabwidget.addTab(persons.Widget(), translate("Competitors"))
        self.results_tab = results.Widget()
        self.tabwidget.addTab(self.results_tab, translate("Race Results"))
        self.tabwidget.addTab(groups.Widget(), translate("Groups"))
        self.tabwidget.addTab(courses.Widget(), translate("Courses"))
        self.tabwidget.addTab(organizations.Widget(), translate("Teams"))
        self.logging_tab = log.Widget()
        self.tabwidget.addTab(self.logging_tab, translate("Logs"))
        self.tabbar = self.tabwidget.tabBar()

        self.tabwidget.currentChanged.connect(self._menu_disable)
        self.tabwidget.currentChanged.connect(self._update_counters)

    def _menu_disable(self, tab_index):
        for item in self.menu_list_for_disabled:
            if tab_index not in item[1]:
                item[0].setDisabled(True)
            else:
                item[0].setDisabled(False)
        if tab_index == self.tabwidget.indexOf(self.logging_tab):
            # if self.tabbar.tabTextColor(i) == common_color:
            self.tabbar.setTabTextColor(tab_index, self.logging_tab.common_color)

    def _update_counters(self, tab_index):
        if tab_index > 1:
            # calculate group, team and course statistics only when tabs activated not to hang application
            race().update_counters()
            self.refresh()

    def get_size(self):
        return {
            # 'x': self.x() + 8,
            "x": self.geometry().x(),
            # 'y': self.y() + 30,
            "y": self.geometry().y(),
            "width": self.width(),
            "height": self.height(),
        }

    def set_title(self, title=None):
        main_title = "{} {}".format(config.NAME, config.VERSION)
        if title:
            self.setWindowTitle("{} - {}".format(title, main_title))
        elif self.file:
            self.set_title(
                "{} [{}]".format(race().data.get_start_datetime(), self.file)
            )
        else:
            self.setWindowTitle(main_title)

    def statusbar_message(self, msg, msecs=5000):
        if hasattr(self, "statusbar"):
            self.statusbar.showMessage("", 0)
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
            logging.error("{} {}".format(index, translate("Tab doesn't exist")))

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

            obj = race()
            if obj.data.race_type == RaceType.MULTI_DAY_RACE:
                day_index = get_current_race_index()
                for i in range(len(races())):
                    set_current_race_index(i)
                    race().rebuild_indexes()
                    recalculate_results(race_object=race())
                set_current_race_index(day_index)
            else:
                obj.rebuild_indexes(True, True)

        except Exception as e:
            logging.error(str(e))

    def refresh_by_timer(self):
        self.refresh()
        self.refresh_timer.stop()

    def deleyed_refresh(self, delay=1000):  # msec
        self.refresh_timer.start(delay)

    def res_recalculate_by_timer(self):
        recalculate_results(recheck_results=False)
        self.res_recalculate.stop()

    def deleyed_res_recalculate(self, delay=1000):  # msec
        self.res_recalculate.start(delay)

    def refresh(self):
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

            logging.debug("Refresh in %s seconds", "{:.3f}".format(time.time() - t))
            self.get_result_table().update_splits()
        except Exception as e:
            logging.error(str(e))

    def clear_filters(self, remove_condition=True):
        if self.get_person_table():
            self.get_person_table().model().clear_filter(remove_condition)
            self.get_result_table().model().clear_filter(remove_condition)
            self.get_group_table().model().clear_filter(remove_condition)
            self.get_course_table().model().clear_filter(remove_condition)
            self.get_organization_table().model().clear_filter(remove_condition)

    def apply_filters(self):
        if self.get_person_table():
            self.get_person_table().model().apply_filter()
            self.get_result_table().model().apply_filter()
            self.get_group_table().model().apply_filter()
            self.get_course_table().model().apply_filter()
            self.get_organization_table().model().apply_filter()

    def add_recent_file(self, file):
        self.delete_from_recent_files(file)
        self.recent_files.insert(0, file)
        Configuration().parser[ConfigFile.PATH] = {"recent_files": self.recent_files}

    def delete_from_recent_files(self, file):
        if file in self.recent_files:
            self.recent_files.remove(file)

    def get_table_by_name(self, name):
        return self.findChild(QtWidgets.QTableView, name)

    def get_person_table(self):
        return self.get_table_by_name("PersonTable")

    def get_result_table(self):
        return self.get_table_by_name("ResultTable")

    def get_group_table(self):
        return self.get_table_by_name("GroupTable")

    def get_course_table(self):
        return self.get_table_by_name("CourseTable")

    def get_organization_table(self):
        return self.get_table_by_name("OrganizationTable")

    def get_current_table(self):
        map_ = [
            "PersonTable",
            "ResultTable",
            "GroupTable",
            "CourseTable",
            "OrganizationTable",
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

    def clear_selection(self, table=None):
        if table is None:
            table = self.get_current_table()
        table.clearSelection()

    def add_sportident_result_from_sireader(self, result):
        try:
            assignment_mode = race().get_setting("system_assignment_mode", False)
            if not assignment_mode:
                self.clear_filters(remove_condition=False)
                rg = ResultSportidentGeneration(result)
                if rg.add_result():
                    result = rg.get_result()
                    recalculate_results(recheck_results=False)
                    if race().get_setting("split_printout", False):
                        try:
                            split_printout([result])
                        except NoResultToPrintException as e:
                            logging.exception(e)
                        except NoPrinterSelectedException as e:
                            logging.exception(e)
                        except Exception as e:
                            logging.exception(e)
                    elif result.person and result.person.group:
                        GroupSplits(race(), result.person.group).generate(True)
                    Teamwork().send(result.to_dict())
                    live_client.send(result)
                    telegram_client.send_result(result)
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
                selection = mv.get_selected_rows(mv.get_table_by_name("PersonTable"))
                if selection:
                    for i in selection:
                        if i < len(race().persons):
                            cur_person = race().persons[i]
                            if cur_person.card_number:
                                confirm = messageBoxQuestion(
                                    self,
                                    translate("Question"),
                                    translate(
                                        "Are you sure you want to reassign the chip number"
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
                            old_person = race().person_card_number(
                                person, result.card_number
                            )
                            if old_person:
                                Teamwork().send(old_person.to_dict())
                            person.is_rented_card = True
                            Teamwork().send(person.to_dict())
                            live_client.send(person)
                            break
            self.refresh()
        except Exception as e:
            logging.exception(e)

    def add_sfr_result_from_reader(self, result):
        self.add_sportident_result_from_sireader(result)

    def add_sportiduino_result_from_reader(self, result):
        self.add_sportident_result_from_sireader(result)

    def add_impinj_result_from_reader(self, result):
        self.add_sportident_result_from_sireader(result)

    def add_srpid_result_from_reader(self, result):
        self.add_sportident_result_from_sireader(result)

    # Actions
    def create_file(self, *args, update_data=True, is_new=False):
        file_name = get_save_file_name(
            translate("Create SportOrg file"),
            translate("SportOrg file (*.json)"),
            time.strftime("%Y%m%d"),
        )
        if file_name:
            try:
                # protect from overwriting with empty file
                if is_new and os.path.exists(file_name):
                    if os.path.getsize(file_name) > 1000:
                        QMessageBox.warning(
                            self,
                            translate("Error"),
                            translate("Cannot overwrite existing file with new")
                            + ": "
                            + file_name,
                        )
                        return

                if not self.lock_file(file_name):
                    return

                if update_data:
                    new_event([Race()])
                    set_current_race_index(0)
                self.clear_filters(remove_condition=False)
                File(file_name).create()
                self.apply_filters()
                self.last_update = time.time()
                self.file = file_name
                self.add_recent_file(self.file)
                self.set_title()
                self.init_model()
            except Exception as e:
                logging.exception(e)
                QMessageBox.warning(
                    self,
                    translate("Error"),
                    translate("Cannot create file") + ": " + file_name,
                )
            self.refresh()

    def save_file_as(self):
        self.create_file(update_data=False, is_new=False)

    def save_file(self):
        if self.file:
            try:
                self.clear_filters(remove_condition=False)
                File(self.file).save()
                self.apply_filters()
                self.last_update = time.time()
            except Exception as e:
                logging.exception(e)
        else:
            self.save_file_as()

    def open_file(self, file_name=None):
        if file_name:
            try:
                if not self.lock_file(file_name):
                    return

                File(file_name).open()
                self.file = file_name
                self.set_title()
                self.add_recent_file(self.file)
                self.init_model()
                self.last_update = time.time()
            except Exception as e:
                logging.exception(e)
                self.delete_from_recent_files(file_name)
                QMessageBox.warning(
                    self,
                    translate("Error"),
                    translate("Cannot read file, format unknown") + ": " + file_name,
                )

    def split_printout_selected(self):
        if self.current_tab != 1:
            logging.warning(translate("No result selected"))
            return
        try:
            indexes = self.get_selected_rows()
            obj = race()
            print_results = []
            for index in indexes:
                if index < 0:
                    continue
                if index >= len(obj.results):
                    pass
                # self.split_printout(obj.results[index])
                print_results.append(obj.results[index])

            confirm_printing = True
            if len(print_results) > 1:
                confirm = messageBoxQuestion(
                    self,
                    translate("Question"),
                    translate("Please confirm"),
                    QMessageBox.Yes | QMessageBox.No,
                )
                confirm_printing = confirm == QMessageBox.Yes
            if confirm_printing:
                split_printout(print_results)

        except Exception as e:
            logging.exception(str(e))

    def split_printout(self, results):
        try:
            split_printout(results)
        except NoResultToPrintException as e:
            logging.warning(str(e))
            mes = QMessageBox(self)
            mes.setText(translate("No results to print"))
            mes.exec_()
        except NoPrinterSelectedException as e:
            logging.warning(str(e))
            mes = QMessageBox(self)
            mes.setText(translate("No printer selected"))
            mes.exec_()

    def add_object(self):
        try:
            tab = self.current_tab
            if tab == 0:
                p = race().add_new_person()
                PersonEditDialog(p, True).exec_()
                self.refresh()
            elif tab == 1:
                self.menu_factory.execute("ManualFinishAction")
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
            logging.exception(e)

    def delete_object(self):
        try:
            if self.current_tab not in range(5):
                return
            self._delete_object()
        except Exception as e:
            logging.exception(e)

    def _delete_object(self):
        indexes = self.get_selected_rows()
        if not len(indexes):
            return

        confirm = messageBoxQuestion(
            self,
            translate("Question"),
            translate("Please confirm"),
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.No:
            return
        tab = self.current_tab
        res = []
        if tab == 0:
            res = race().delete_persons(indexes)
            recalculate_results(recheck_results=False)
            live_client.delete(res)
            race().rebuild_indexes()
        elif tab == 1:
            res = race().delete_results(indexes)
            recalculate_results(recheck_results=False)
            live_client.delete(res)
        elif tab == 2:
            try:
                res = race().delete_groups(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(
                    self.get_group_table(),
                    translate("Error"),
                    translate("Cannot remove group"),
                )
        elif tab == 3:
            try:
                res = race().delete_courses(indexes)
                race().rebuild_indexes(False, True)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(
                    self.get_course_table(),
                    translate("Error"),
                    translate("Cannot remove course"),
                )
        elif tab == 4:
            try:
                res = race().delete_organizations(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(
                    self.get_organization_table(),
                    translate("Error"),
                    translate("Cannot remove organization"),
                )

        self.clear_selection()
        self.refresh()
        if len(res):
            Teamwork().delete([r.to_dict() for r in res])

    def get_split_printer_thread(self):
        return self.split_printer_thread

    def set_split_printer_thread(self, split_printer):
        self.split_printer_thread = split_printer

    def get_split_printer_queue(self):
        return self.split_printer_queue

    def set_split_printer_queue(self, split_printer_app):
        self.split_printer_queue = split_printer_app

    def lock_file(self, file_name: str):
        logging.info("lock start")
        if self.file == file_name:
            # already locked by current process ('Save as' or 'Open' for the same file)
            return True

        # unlock previously locked file (e.g. in case of 'save as' operation)
        self.unlock_file(self.file)

        # try to acquire the lock on a single file path
        lockfile = file_name + ".lock"
        if exists(lockfile):
            with open(lockfile) as f:
                pid = f.read()
                if pid.isdigit() and psutil.pid_exists(int(pid)):
                    # already locked = opened in another process, avoid parallel opening

                    p = Process(int(pid))
                    logging.info("found process %s", str(p))

                    QMessageBox.warning(
                        self,
                        translate("Error"),
                        translate("Cannot open file, already locked")
                        + ": "
                        + file_name,
                    )
                    return False

        # new lock creating
        with open(lockfile, "w") as f:
            f.write(str(os.getpid()))
        return True

    def unlock_file(self, file_name):
        if file_name:
            lockfile = file_name + ".lock"
            if exists(lockfile):
                remove(lockfile)
