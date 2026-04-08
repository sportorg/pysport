import datetime
import logging
import time
from queue import Empty, Queue
from threading import Event, main_thread

import serial

try:
    from PySide6.QtCore import QThread, Signal
except ModuleNotFoundError:
    from PySide2.QtCore import QThread, Signal

from sportorg.libs.huichang.huichang import (
    Huichang,
    HuichangException,
    HuichangTimeout,
)

from sportorg.common.singleton import singleton
from sportorg.models import memory
from sportorg.modules.sportident import backup
from sportorg.utils.time import time_to_otime


class HuichangCommand:
    def __init__(self, command, data=None):
        self.command = command
        self.data = data


class HuichangThread(QThread):
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
            hc = Huichang(port=self.port, logger=logging.root)
        except Exception as e:
            self._logger.error(str(e))
            return

        while not self._stop_event.is_set():
            try:
                self._wait_card_data(hc)
            except HuichangException as e:
                self._logger.error(str(e))
            except serial.serialutil.SerialException as e:
                self._logger.error(str(e))
                break
            except Exception as e:
                self._logger.error(str(e))
                break
        hc.disconnect()
        self._logger.debug("Stop Huichang reader")

    def _wait_card_data(self, hc):
        while not (card_data := hc.wait_card_data()):
            time.sleep(0.5)
            if not main_thread().is_alive() or self._stop_event.is_set():
                return
        self._queue.put(HuichangCommand("card_data", card_data), timeout=1)


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
                self._logger.error(str(e))
                raise e
        self._logger.debug("Stop adder result")

    @staticmethod
    def _get_result(card_data):
        result = memory.race().new_result(memory.ResultSportiduino)
        result.card_number = int(card_data["card_number"])

        for i in range(len(card_data["punches"])):
            t = card_data["punches"][i][1]
            if t:
                split = memory.Split()
                split.code = str(card_data["punches"][i][0])
                split.time = time_to_otime(t)
                split.days = memory.race().get_days(t)
                result.splits.append(split)

        if "start" in card_data and card_data["start"]:
            result.start_time = time_to_otime(card_data["start"])
        if "finish" in card_data and card_data["finish"]:
            result.finish_time = time_to_otime(card_data["finish"])
        # if 'battery_level' in card_data:
        #    result.card_battery_level = max(0, min(100, card_data['battery_level']))

        return result


@singleton
class HuichangClient:
    def __init__(self):
        self._queue = Queue()
        self._stop_event = Event()
        self._huichang_thread = None
        self._result_thread = None
        self.port = None
        self._logger = logging.root
        self._call_back = None

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def _start_huichang_thread(self):
        if self._huichang_thread is None:
            self._huichang_thread = HuichangThread(
                self.port, self._queue, self._stop_event, self._logger, debug=True
            )
            self._huichang_thread.start()
        elif self._huichang_thread.isFinished():
            self._huichang_thread = None
            self._start_huichang_thread()

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
        elif self._result_thread.isFinished():
            self._result_thread = None
            self._start_result_thread()

    def is_alive(self):
        if self._huichang_thread and self._result_thread:
            return (
                not self._huichang_thread.isFinished()
                and not self._result_thread.isFinished()
            )

        return False

    def start(self):
        self.port = self.choose_port()
        self._stop_event.clear()
        self._start_huichang_thread()
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
