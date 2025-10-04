import logging
import os
import subprocess
import time
from queue import Empty, Queue
from threading import Event, main_thread
from time import sleep
import bluetooth
import yaml

from sportorg.gui.global_access import GlobalAccess

try:
    from PySide6.QtCore import QThread, Signal
    from PySide6.QtWidgets import QMessageBox
except ModuleNotFoundError:
    from PySide2.QtCore import QThread, Signal
    from PySide2.QtWidgets import QMessageBox

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
    def __init__(self, file_name, separator, queue, stop_event, logger, debug=False):
        super().__init__()
        self.setObjectName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger
        self._debug = debug
        self.file_name = file_name
        self.separator = separator

    def run(self):
        try:
            ruident = Ruident(data_file=self.file_name, separator=self.separator, debug=True, logger=logging.root)
        except Exception as e:
            self._logger.exception(e)
            return

        try:
            while True:
                if not main_thread().is_alive() or self._stop_event.is_set():
                    ruident.disconnect()
                    self._logger.info("RUIDENT: stopping reader")
                    return
                card_data_array = ruident.get_next_data()
                if card_data_array:
                    for card_data in card_data_array:
                        self._queue.put(
                            RuidentCommand("card_data", card_data), timeout=1
                        )
                else:
                    # no data, wait 1 second before repeating
                    sleep(1)

        except Exception as e:
            self._logger.exception(e)


class ResultThread(QThread):
    data_sender = Signal(object)

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
        self.file_name = None
        self.separator = ";"

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def _start_ruident_thread(self):
        if self._ruident_thread is None:

            # self.file_name = get_open_file_name()

            # check bluetooth
            if not self.check_bluetooth():
                QMessageBox.critical(None, "Error", f"Please enable Bluetooth and try again")

            # start reader (external app)
            self.launch_reader_service()

            # open results tab
            GlobalAccess().get_main_window().select_tab(1)

            # show icon on toolbar
            GlobalAccess().get_main_window().sportident_icon = {
                True: "ruident.png",
                False: "sportident.png",
            }


            self._ruident_thread = RuidentThread(
                self.file_name, self.separator, self._queue, self._stop_event, self._logger, debug=True
            )
            self._ruident_thread.start()
        elif self._ruident_thread.isFinished():
            self._ruident_thread = None
            self._start_ruident_thread()

    def _start_result_thread(self):
        if self._result_thread is None:
            self._result_thread = ResultThread(
                self._queue,
                self._stop_event,
                self._logger,
            )
            if self._call_back:
                self._result_thread.data_sender.connect(self._call_back)
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

    def start(self):
        # self.port = self.choose_port()
        self._stop_event.clear()
        self._start_ruident_thread()
        self._start_result_thread()

    def stop(self):
        self._stop_event.set()

    def toggle(self):
        if self.is_alive():
            self.stop()
            return
        self.start()

    def choose_port(self):
        return memory.race().get_setting("system_port", None)

    def launch_reader_service(self):
        cwd = os.getcwd()
        ruident_folder = cwd + os.path.sep + "ruident"
        if os.path.isdir(ruident_folder):
            ruident_exe = ruident_folder + os.path.sep + "RuidConnectRD.exe"
            if os.path.isfile(ruident_exe):
                try:
                    progs = str(subprocess.check_output('tasklist'))
                    if "RuidConnectRD.exe" not in progs:
                        self._logger.info(f"RUIDENT: starting RuidConnectRD.exe")
                        os.chdir(ruident_folder)
                        os.system("start cmd /k " + ruident_exe)
                        os.chdir(cwd)
                    else:
                        self._logger.info(f"RUIDENT: RuidConnectRD.exe already started")
                except Exception as e:
                    self._logger.exception(e)

            ruident_config = ruident_folder + os.path.sep + "config.yaml"
            if os.path.isfile(ruident_config):
                with open(ruident_config) as stream:
                    try:
                        config = yaml.safe_load(stream)
                        out_path = config["export"]["out_path"]
                        is_date_delimit = config["export"]["is_date_delimit"]
                        self.separator = config["export"]["delimiter"]
                        if is_date_delimit:
                            self.file_name = out_path + os.path.sep + time.strftime("data_%Y_%m_%d.csv")
                        else:
                            self.file_name = out_path + os.path.sep + "data.csv"

                        if not os.path.exists(self.file_name):
                            sleep(1)
                            if not os.path.exists(self.file_name):
                                self.file_name = get_open_file_name()

                    except yaml.YAMLError as e:
                        print(e)
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
