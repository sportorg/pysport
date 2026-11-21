import logging
import queue
import time
from queue import Empty, Queue
from random import randint
from threading import Event, main_thread
from time import sleep

import serial

from sportorg.libs.rfid_impinj.pyImpinj import ImpinjR2KReader, ImpinjR2KFastSwitchInventory

try:
    from PySide6.QtCore import QThread, Signal
except ModuleNotFoundError:
    from PySide2.QtCore import QThread, Signal


except ModuleNotFoundError:
    ImpinjR2KReader = None
    ImpinjR2KFastSwitchInventory = None

from sportorg.common.otime import OTime
from sportorg.common.singleton import singleton
from sportorg.models import memory


class ImpinjCommand:
    def __init__(self, command, data=None):
        self.command = command
        self.data = data


class ImpinjThread(QThread):
    def __init__(self, port, queue, stop_event, logger, debug=False):
        self.port = port
        super().__init__()
        self.setObjectName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger
        self._debug = debug


    def run(self):
        if not ImpinjR2KReader or not ImpinjR2KFastSwitchInventory:
            return
        try:
            tag_queue = queue.Queue(1024)
            impinj_reader = ImpinjR2KReader(tag_queue, address=1)

            try:
                impinj_reader.connect(self.port)
            except BaseException as err:
                logging.exception(str(err))
                return

            impinj_reader.worker_start()
            # impinj_reader.fast_power(22)

        except Exception as e:
            self._logger.error(str(e))
            return

        while True:
            if not main_thread().is_alive() or self._stop_event.is_set():
                impinj_reader.worker_close()
                self._logger.debug("Stop Impinj reader")
                return

            try:
                data = tag_queue.get(timeout=0.1)
            except Exception:
                impinj_reader.fast_switch_ant_inventory(
                    param=dict(
                        A=ImpinjR2KFastSwitchInventory.ANTENNA1,
                        Aloop=1,
                        B=ImpinjR2KFastSwitchInventory.ANTENNA2,
                        Bloop=1,
                        C=ImpinjR2KFastSwitchInventory.ANTENNA3,
                        Cloop=1,
                        D=ImpinjR2KFastSwitchInventory.ANTENNA4,
                        Dloop=1,
                        E=ImpinjR2KFastSwitchInventory.ANTENNA5,
                        Eloop=1,
                        F=ImpinjR2KFastSwitchInventory.ANTENNA6,
                        Floop=1,
                        G=ImpinjR2KFastSwitchInventory.ANTENNA7,
                        Gloop=1,
                        H=ImpinjR2KFastSwitchInventory.ANTENNA8,
                        Hloop=1,
                        Interval=0,
                        Repeat=1,
                    )
                )
                continue

            try:
                self._logger.debug("Impinj RFID data: {}".format(data))
                card_data = data
                card_data["time"] = OTime.now()
                self._queue.put(ImpinjCommand("card_data", card_data), timeout=1)

            except serial.serialutil.SerialException as e:
                self._logger.error(str(e))
                return
            except Exception as e:
                self._logger.error(str(e))

    def run_test(self):
        while True:
            if not main_thread().is_alive() or self._stop_event.is_set():
                self._logger.debug("Stop Impinj reader")
                return
            try:
                sleep(1)
                card_data = {}
                card_data["time"] = OTime.now()
                epc_list = [
                    "00 00 00 01",
                    "00 00 00 14",
                    "00 00 00 0E",
                    "BFACACACACACACACACA",
                ]
                card_data["epc"] = epc_list[randint(0, 3)]
                self._queue.put(ImpinjCommand("card_data", card_data), timeout=1)

            except Exception as e:
                self._logger.error(str(e))


class ResultThread(QThread):
    data_sender = Signal(object)

    def __init__(self, queue, stop_event, logger):
        super().__init__()
        self.setObjectName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        time.sleep(1)
        while True:
            try:
                # test generation of punches without equipment
                # remove / comment in release
                # self.test_offline()

                cmd = self._queue.get(timeout=5)
                if cmd.command == "card_data":
                    if cmd.data and "epc" in cmd.data:
                        result = self._get_result(cmd.data)
                        self.data_sender.emit(result)

            except Empty:
                if not main_thread().is_alive() or self._stop_event.is_set():
                    break
            except Exception as e:
                self._logger.exception(e)
        self._logger.debug("Stop adder result")

    # test generation of punches without equipment
    def test_offline(self):
        time.sleep(0.1)
        dummy_data = {'epc':'00 00 00 01', 'time':OTime.now()}
        result = self._get_result(dummy_data)
        create_result= True
        if create_result:
            self.data_sender.emit(result)

    @staticmethod
    def _get_result(card_data):
        result = memory.race().new_result(memory.ResultRfidImpinj)

        limit = 10**8
        hex_offset = 5000000
        epc = str(card_data["epc"]).replace(" ", "")

        # if epc contains only digits, use it directly
        # otherwise convert hex -> dec + add offset
        # 000014 = 14
        # 00000E = 5000014
        if epc.isdecimal():
            result.card_number = int(epc) % limit
        else:
            result.card_number = (int(epc, 16) + hex_offset) % limit

        result.finish_time = card_data["time"]
        return result


@singleton
class ImpinjClient:
    timeout_list = {}
    timeout = 0
    ignore_punches_before_start = False
    static_init = False

    def __init__(self):
        self._queue = Queue()
        self._stop_event = Event()
        self._impinj_thread = None
        self._result_thread = None
        self.port = None
        self._logger = logging.root
        self._call_back = None
        ImpinjClient.static_init = False

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def _start_impinj_thread(self):
        if self._impinj_thread is None:
            self._impinj_thread = ImpinjThread(
                self.port, self._queue, self._stop_event, self._logger, debug=True
            )
            self._impinj_thread.start()
        elif self._impinj_thread.isFinished():
            self._impinj_thread = None
            self._start_impinj_thread()

    def _start_result_thread(self):
        if self._result_thread is None:
            self._result_thread = ResultThread(
                self._queue,
                self._stop_event,
                self._logger,
            )
            if self._call_back is not None:
                self._result_thread.data_sender.connect(self._call_back)
            self._result_thread.start()
        # elif not self._result_thread.is_alive():
        elif self._result_thread.isFinished():
            self._result_thread = None
            self._start_result_thread()

    def is_alive(self):
        if self._impinj_thread is not None and self._result_thread is not None:
            return (
                not self._impinj_thread.isFinished()
                and not self._result_thread.isFinished()
            )

        return False

    def start(self):
        self.port = self.choose_port()
        self._stop_event.clear()
        self._start_impinj_thread()
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
