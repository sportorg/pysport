import logging
import os
import time
from datetime import datetime, timedelta
from queue import Empty, Queue
from threading import Event, main_thread
from time import sleep

import bluetooth
import pygetwindow
import yaml
from PySide2 import QtGui

from sportorg import config
from sportorg.gui.global_access import GlobalAccess

try:
    from PySide6.QtCore import QThread, Signal
    from PySide6.QtWidgets import QMessageBox, QApplication
except ModuleNotFoundError:
    from PySide2.QtCore import QThread, Signal
    from PySide2.QtWidgets import QMessageBox, QApplication

from sportorg.common.singleton import singleton
from sportorg.gui.dialogs.file_dialog import get_open_file_name
from sportorg.libs.ruident.ruident import Ruident
from sportorg.models import memory
from sportorg.modules.sportident import backup
from sportorg.utils.time import time_to_otime


class RuidentCommand:
    def __init__(self, command, data=None):
        self.command = command
        self.data = data


class RuidentThread(QThread):
    def __init__(self, file_name, separator, queue, stop_event, logger, debug=False, timeout=0):
        super().__init__()
        self.setObjectName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger
        self._debug = debug
        self.file_name = file_name
        self.separator = separator
        self.timeout = timeout

    def run(self):
        self._logger.info(f"RUIDENT: starting reader with timeout {self.timeout} seconds")
        try:
            ruident = Ruident(data_file=self.file_name, separator=self.separator, debug=True, logger=logging.root,
                              timeout_sec=self.timeout)
        except Exception as e:
            self._logger.exception(e)
            return

        try:
            su_event_count = 0
            minimize_window_time = None
            while True:
                if not main_thread().is_alive() or self._stop_event.is_set():
                    ruident.disconnect()
                    self._logger.info("RUIDENT: stopping reader")
                    return
                card_data_array = ruident.get_next_data()

                if minimize_window_time is not None and minimize_window_time < datetime.now():
                    minimize_window_time = None
                    RuidentClient().minimize_ruident_utility()

                if card_data_array:
                    su_event_count = 0
                    for card_data in card_data_array:
                        self._queue.put(
                            RuidentCommand("card_data", card_data), timeout=1
                        )
                    self._queue.put(
                        RuidentCommand("smile_icon", None), timeout=1
                    )
                    # got data from utility, wait 3 seconds and minimize window
                    if minimize_window_time is None and not RuidentClient().is_window_minimized():
                        minimize_window_time = datetime.now() + timedelta(seconds=3)
                else:
                    # no data, wait 1 second before repeating
                    sleep(1)
                    self._queue.put(
                        RuidentCommand("ruident_icon", None), timeout=1
                    )
                    cur_time = datetime.now()
                    timeout = 10
                    if ruident.last_utility_time is None:
                        ruident.last_utility_time = cur_time
                    if ruident.last_utility_time and ruident.last_utility_time + timedelta(seconds=timeout) < cur_time:
                        self._logger.info(f"RUIDENT: no SU signal from station for more than {timeout} seconds!")

                        # self._queue.put(
                        #     RuidentCommand("smile_icon", None), timeout=1
                        # )

                        ruident.last_utility_time = cur_time
                        su_event_count += 1

                    if su_event_count > 1:
                        # show Ruident utility after 2 SU missed events

                        if RuidentClient().is_window_launched():
                            RuidentClient().show_ruident_utility()
                            self._logger.info(f'RUIDENT: No data received from reader station. You may need to '
                                              f'activate or restart reader station. Your reader station can also be '
                                              f'connected to other access point. Disconnect and restart.')
                        else:
                            self._logger.info(f"RUIDENT: RuidConnectRD utility is closed, please restart "
                                              f"Ruident Service.")

                        su_event_count = 0

        except Exception as e:
            self._logger.exception(e)


class ResultThread(QThread):
    data_sender = Signal(object)
    data_sender_icon_smile = Signal()
    data_sender_icon_ruident = Signal()

    def __init__(self, queue, stop_event, logger):
        super().__init__()
        self.setObjectName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        time.sleep(3)
        while True:
            try:
                cmd = self._queue.get(timeout=5)
                if cmd.command == "card_data":
                    result = self._get_result(cmd.data)
                    self.data_sender.emit(result)
                    backup.backup_data(cmd.data)
                if cmd.command == "smile_icon":
                    self.data_sender_icon_smile.emit()
                if cmd.command == "ruident_icon":
                    self.data_sender_icon_ruident.emit()
            except Empty:
                if not main_thread().is_alive() or self._stop_event.is_set():
                    break
            except Exception as e:
                self._logger.exception(e)
                raise e
        self._logger.debug("Stop adder result")

    @staticmethod
    def _get_result(card_data):
        result = memory.race().new_result(memory.ResultRuident)
        if "card_number" not in card_data:
            return None

        result.card_number = int(card_data["card_number"])

        for i in range(len(card_data["punches"])):
            t = card_data["punches"][i][1]
            if t:
                split = memory.Split()
                split.code = str(card_data["punches"][i][0])
                split.time = time_to_otime(t)
                split.days = memory.race().get_days(t)
                result.splits.append(split)
        if "start" in card_data:
            result.start_time = time_to_otime(card_data["start"])
        if "finish" in card_data:
            result.finish_time = time_to_otime(card_data["finish"])
        return result


@singleton
class RuidentClient:
    def __init__(self):
        self._queue = Queue()
        self._stop_event = Event()
        self._ruident_thread = None
        self._result_thread = None
        # self.port = None
        self._logger = logging.root
        self._call_back = None
        self._call_back_icon_smile = self.set_icon_smile
        self._call_back_icon_ruident = self.set_icon_ruident
        self.file_name = None
        self.separator = ";"

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def _start_ruident_thread(self, timeout=0):
        if self._ruident_thread is None:

            # self.file_name = get_open_file_name()

            # check bluetooth
            if not self.check_bluetooth():
                QMessageBox.critical(None, "Error", f"Please enable Bluetooth and try again")

            # start reader (external app)
            self.launch_reader_service()

            # open results tab
            GlobalAccess().get_main_window().select_tab(5)

            # show icon on toolbar
            self.set_icon_ruident()

            self._ruident_thread = RuidentThread(
                self.file_name, self.separator, self._queue, self._stop_event, self._logger, debug=True, timeout=timeout
            )
            self._ruident_thread.start()
        else:
            if self._ruident_thread.isFinished():
                self._ruident_thread = None
                self._start_ruident_thread(timeout=timeout)
            else:
                self._ruident_thread.timeout = timeout

    def _start_result_thread(self):
        if self._result_thread is None:
            self._result_thread = ResultThread(
                self._queue,
                self._stop_event,
                self._logger,
            )
            if self._call_back:
                self._result_thread.data_sender.connect(self._call_back)
            if self._call_back_icon_ruident:
                self._result_thread.data_sender_icon_ruident.connect(self._call_back_icon_ruident)
            if self._call_back_icon_smile:
                self._result_thread.data_sender_icon_smile.connect(self._call_back_icon_smile)
            self._result_thread.start()
        # elif not self._result_thread.is_alive():
        elif self._result_thread.isFinished():
            self._result_thread = None
            self._start_result_thread()

    def is_alive(self):
        if self._ruident_thread and self._result_thread:
            return (
                    not self._ruident_thread.isFinished()
                    and not self._result_thread.isFinished()
            )

        return False

    def start(self, timeout=0):
        # self.port = self.choose_port()
        self._stop_event.clear()
        self._start_ruident_thread(timeout=timeout)
        self._start_result_thread()

    def stop(self):
        self._stop_event.set()

    @staticmethod
    def stop_ruident_utility():
        service_name = "RuidConnectRD.exe"
        # Find the window by title (case-insensitive)
        for window in pygetwindow.getWindowsWithTitle(service_name):
            # Close the window
            window.close()

    @staticmethod
    def minimize_ruident_utility():
        service_name = "RuidConnectRD.exe"
        # Find the window by title (case-insensitive)
        for window in pygetwindow.getWindowsWithTitle(service_name):
            # minimize all windows
            window.minimize()

    @staticmethod
    def show_ruident_utility():
        service_name = "RuidConnectRD.exe"
        # Find the window by title (case-insensitive)
        for window in pygetwindow.getWindowsWithTitle(service_name):
            # maximize first found window
            window.restore()
            try:
                window.activate()
            except Exception as e:
                logging.info("Cannot open window, SportOrg is not active now")
            break

    def toggle(self):
        if self.is_alive():
            self.stop()
            return
        self.start()

    @staticmethod
    def choose_port():
        return memory.race().get_setting("system_port", None)

    def get_data_filepath(self):
        cwd = os.getcwd()
        ruident_folder = cwd + os.path.sep + "ruident"
        ruident_config = ruident_folder + os.path.sep + "config.yaml"
        if os.path.isfile(ruident_config):
            with open(ruident_config) as stream:
                try:
                    config = yaml.safe_load(stream)
                    out_path = config["export"]["out_path"]
                    is_date_delimit = config["export"]["is_date_delimit"]
                    self.separator = config["export"]["delimiter"]

                    if out_path == ".":
                        out_path = ruident_folder

                    if is_date_delimit:
                        self.file_name = out_path + os.path.sep + time.strftime("data_%Y_%m_%d.csv")
                    else:
                        self.file_name = out_path + os.path.sep + "data.csv"

                except Exception as e:
                    self._logger.exception(e)

    def launch_reader_service(self):
        cwd = os.getcwd()
        ruident_folder = cwd + os.path.sep + "ruident"
        if os.path.isdir(ruident_folder):
            ruident_exe = ruident_folder + os.path.sep + "RuidConnectRD.exe"
            if os.path.isfile(ruident_exe):
                try:
                    app_list = pygetwindow.getWindowsWithTitle('RuidConnectRD.exe')
                    if len(app_list) == 0:
                        self._logger.info(f"RUIDENT: starting RuidConnectRD.exe")
                        os.chdir(ruident_folder)
                        # os.system("start cmd /k " + ruident_exe)
                        os.startfile(ruident_exe)
                        os.chdir(cwd)
                    else:
                        self._logger.info(f"RUIDENT: RuidConnectRD.exe already started")
                except Exception as e:
                    self._logger.exception(e)

            self.get_data_filepath()

            if not os.path.exists(self.file_name):
                sleep(1)
                if not os.path.exists(self.file_name):
                    self.file_name = get_open_file_name()

            if not self.file_name:
                self.file_name = get_open_file_name()

    def check_bluetooth(self):
        try:
            adapters = bluetooth.read_local_bdaddr()
            if adapters:
                self._logger.info(f"RUIDENT: Bluetooth adapter detected: {adapters[0]}")
                return True
            else:
                self._logger.info(f"RUIDENT: Bluetooth adapter not found or disabled")

        except bluetooth.BluetoothError as e:
            self._logger.info(f"RUIDENT: Error with Bluetooth: {e}")
        except Exception as e:
            self._logger.info(f"RUIDENT: Unexpected Bluetooth error: {e}")
        return False

    def set_icon_smile(self):
        self._logger.info(f"RUIDENT: smile!")
        GlobalAccess().get_main_window().sportident_icon = {
            True: "ruident_ok.png",
            False: "sportident.png",
        }
        # GlobalAccess().get_main_window().interval()
        GlobalAccess().get_main_window().toolbar_property["sportident"].setIcon(
            QtGui.QIcon(
                config.icon_dir(GlobalAccess().get_main_window().sportident_icon[True])
            )
        )


    def set_icon_ruident(self):
        # self._logger.info(f"RUIDENT: ruident 1!")
        GlobalAccess().get_main_window().sportident_icon = {
            True: "ruident.png",
            False: "sportident.png",
        }
        # GlobalAccess().get_main_window().interval()
        GlobalAccess().get_main_window().toolbar_property["sportident"].setIcon(
            QtGui.QIcon(
                config.icon_dir(GlobalAccess().get_main_window().sportident_icon[True])
            )
        )

    @staticmethod
    def is_window_minimized():
        service_name = "RuidConnectRD.exe"
        # Find the window by title (case-insensitive)
        for window in pygetwindow.getWindowsWithTitle(service_name):
            # check first found window to be maximized
            return window.isMinimized

        return False

    @staticmethod
    def is_window_launched():
        service_name = "RuidConnectRD.exe"
        # Find the window by title (case-insensitive)
        return len(pygetwindow.getWindowsWithTitle(service_name)) > 0
