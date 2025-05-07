import logging
import time
from queue import Empty, Queue
from threading import Event, main_thread

import serial

try:
    from PySide6.QtCore import QThread, Signal
except ModuleNotFoundError:
    from PySide2.QtCore import QThread, Signal

from sportorg.common.singleton import singleton
from sportorg.libs.srpid.srpid import SRPid, SRPidException
from sportorg.models import memory
from sportorg.modules.sportident import backup
from sportorg.utils.time import time_to_otime


class SrpidCommand:
    def __init__(self, command, data=None):
        self.command = command
        self.data = data


class SrpidThread(QThread):
    def __init__(self, port, queue, stop_event, logger, debug=False):
        self.port = port
        super().__init__()
        self.setObjectName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger
        self._debug = debug

    def run(self):
        try:
            srpid = SRPid(port=self.port, debug=True, logger=logging.root)
        except Exception as e:
            self._logger.exception(e)
            return

        while True:
            try:
                while not srpid.search_chip():
                    time.sleep(0.5)
                    if not main_thread().is_alive() or self._stop_event.is_set():
                        srpid.disconnect()
                        self._logger.debug("Stop srpid reader")
                        return
                card_data = srpid.chip_data
                self._queue.put(SrpidCommand("card_data", card_data), timeout=1)
                srpid.beep_ok()
            except SRPidException as e:
                self._logger.exception(e)
            except serial.serialutil.SerialException as e:
                self._logger.exception(e)
                return
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
                    backup.backup_data(convert_data(cmd.data))
            except Empty:
                if not main_thread().is_alive() or self._stop_event.is_set():
                    break
            except Exception as e:
                self._logger.exception(e)
                raise e
        self._logger.debug("Stop adder result")

    @staticmethod
    def _get_result(card_data):
        result = memory.race().new_result(memory.ResultSrpid)
        result.card_number = int(card_data["ChipNum"])

        for i in range(len(card_data["CP"])):
            t = card_data["CP"][i][1]
            if t:
                # !
                # НОМЕРА СТАНЦИЙ SRPid
                # ------------------------------
                # 1...200 ОТМЕТКА
                #
                # 241  СТАРТ
                # 242  ФИНИШ
                # !

                split = memory.Split()
                split.code = str(card_data["CP"][i][0])
                split.time = time_to_otime(t)
                split.days = memory.race().get_days(t)

                if split.code == "241":
                    result.start_time = time_to_otime(t)
                elif split.code == "242":
                    result.finish_time = time_to_otime(t)
                else:
                    result.splits.append(split)

        return result


@singleton
class SrpidClient:
    def __init__(self):
        self._queue = Queue()
        self._stop_event = Event()
        self._srpid_thread = None
        self._result_thread = None
        self.port = None
        self._logger = logging.root
        self._call_back = None

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def _start_srpid_thread(self):
        if self._srpid_thread is None:
            self._srpid_thread = SrpidThread(
                self.port, self._queue, self._stop_event, self._logger, debug=True
            )
            self._srpid_thread.start()
        elif self._srpid_thread.isFinished():
            self._srpid_thread = None
            self._start_srpid_thread()

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
        if self._srpid_thread and self._result_thread:
            return (
                not self._srpid_thread.isFinished()
                and not self._result_thread.isFinished()
            )

        return False

    def start(self):
        self.port = self.choose_port()
        self._stop_event.clear()
        self._start_srpid_thread()
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


def convert_data(data):
    # convert SRpid data to classic SPORTident-like data
    # ChipNum -> card_number
    # CP -> punches

    new_data = {"card_number": "0", "punches": {}}
    if not data:
        return new_data

    if "ChipNum" in data:
        new_data["card_number"] = data["ChipNum"]
    if "CP" in data:
        new_data["punches"] = data["CP"]
    return new_data
