import datetime
import logging
import os
import platform
import re
import time
from queue import Empty, Queue
from threading import Event, main_thread

import serial

from sportorg.libs.ruident.ruident import Ruident

try:
    from PySide6.QtCore import QThread, Signal
except ModuleNotFoundError:
    from PySide2.QtCore import QThread, Signal


from sportorg.common.singleton import singleton
from sportorg.language import translate
from sportorg.models import memory
from sportorg.modules.sportident import backup
from sportorg.utils.time import time_to_otime
from serial.tools import list_ports


class RuidentReaderCommand:
    def __init__(self, command, data=None):
        self.command = command
        self.data = data


class RuidentReaderThread(QThread):
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
            reader = Ruident(port=self.port, logger=logging.root)
        except Exception as e:
            self._logger.exception(e)
            return

        max_error = 2000
        error_count = 0

        while True:
            try:
                # read cards in loop
                data = reader.read_data()
                while not data:
                    # no card, sleep and try read again
                    time.sleep(0.2)
                    if not main_thread().is_alive() or self._stop_event.is_set():
                        reader.disconnect()
                        self._logger.debug("Stop Ruident reader")
                        return
                    data = reader.read_data()

                # card registered, get data from reader
                for card_data in data:
                    if (
                        str(card_data["card_number"]).isdigit()
                        and int(card_data["card_number"]) > 0
                    ):
                        self._queue.put(
                            RuidentReaderCommand("card_data", card_data), timeout=1
                        )
                    else:
                        self._logger.debug("Ruident reader error: got 0 card number")
                # reader.ack_sicard()
            except Exception as e:
                self._logger.exception(e)


class RuidentResultThread(QThread):
    data_sender = Signal(object)

    def __init__(self, queue, stop_event, logger, start_time=None):
        super().__init__()
        self.setObjectName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger
        self.start_time = start_time

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
        self._logger.debug("Stop adder result")

    @staticmethod
    def _get_result(card_data):
        result = memory.race().new_result()
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
        else:
            # no finish punch, process
            result.finish_time = None

        return result

    @staticmethod
    def time_to_sec(value, max_val=86400):
        if isinstance(value, datetime.datetime):
            ret = (
                value.hour * 3600
                + value.minute * 60
                + value.second
                + value.microsecond / 1000000
            )
            if max_val:
                ret = ret % max_val
            return ret

        return 0


@singleton
class RuidentClient:
    def __init__(self):
        self._queue = Queue()
        self._stop_event = Event()
        self._reader_thread = None
        self._result_thread = None
        self.port = None
        self._logger = logging.root
        self._call_back = None

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def _start_reader_thread(self):
        if self._reader_thread is None:
            self._reader_thread = RuidentReaderThread(
                self.port, self._queue, self._stop_event, self._logger, debug=True
            )
            self._reader_thread.start()
        elif self._reader_thread.isFinished():
            self._reader_thread = None
            self._start_reader_thread()

    def _start_result_thread(self):
        if self._result_thread is None:
            self._result_thread = RuidentResultThread(
                self._queue, self._stop_event, self._logger, self.get_start_time()
            )
            if self._call_back:
                self._result_thread.data_sender.connect(self._call_back)
            self._result_thread.start()
        elif self._result_thread.isFinished():
            self._result_thread = None
            self._start_result_thread()

    def is_alive(self):
        if self._reader_thread and self._result_thread:
            return (
                not self._reader_thread.isFinished()
                and not self._result_thread.isFinished()
            )

        return False

    def start(self):
        self.port = self.choose_port()
        if self.port:
            self._stop_event.clear()
            self._start_reader_thread()
            self._start_result_thread()
            self._logger.info(translate("Opening port") + " " + self.port)
        else:
            self._logger.info(translate("Cannot open port"))

    def stop(self):
        self._stop_event.set()
        self._logger.info(translate("Closing port"))

    def toggle(self):
        if self.is_alive():
            self.stop()
            return
        self.start()

    @staticmethod
    def get_ports():
        return [port.device for port in list_ports.comports()]

    def choose_port(self):
        si_port = memory.race().get_setting("system_port", "")
        if si_port:
            return si_port
        ports = self.get_ports()
        if len(ports):
            self._logger.info(translate("Available Ports"))
            for i, p in enumerate(ports):
                self._logger.info("{} - {}".format(i, p))
            return ports[0]
        else:
            self._logger.info("No ports available")
            return None

    @staticmethod
    def get_start_time():
        start_time = memory.race().get_setting("system_zero_time", (8, 0, 0))
        return datetime.datetime.today().replace(
            hour=start_time[0],
            minute=start_time[1],
            second=start_time[2],
            microsecond=0,
        )
