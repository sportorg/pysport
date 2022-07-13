import logging
import queue
from queue import Queue, Empty
from random import randint
from threading import main_thread, Event

import time
from time import sleep

import serial
from PySide2.QtCore import QThread, Signal
from pyImpinj import ImpinjR2KReader
from pyImpinj.enums import ImpinjR2KFastSwitchInventory

from sportorg.common.otime import OTime
from sportorg.common.singleton import singleton
from sportorg.models import memory
from sportorg.models.memory import race


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

        self.timeout_list = {}
        self.timeout = race().get_setting('readout_duplicate_timeout', 15000)

    def run(self):
        try:
            tag_queue = queue.Queue(1024)
            impinj_reader = ImpinjR2KReader(tag_queue, address=1)

            try:
                impinj_reader.connect(self.port)
            except BaseException as err:
                print(err)
                return

            impinj_reader.worker_start()
            impinj_reader.fast_power(22)

        except Exception as e:
            self._logger.error(str(e))
            return

        while True:

            if not main_thread().is_alive() or self._stop_event.is_set():
                impinj_reader.worker_close()
                self._logger.debug('Stop Impinj reader')
                return

            try:
                data = tag_queue.get(timeout=0.1)
            except Exception:
                impinj_reader.fast_switch_ant_inventory(param=dict(A=ImpinjR2KFastSwitchInventory.ANTENNA1, Aloop=1,
                                                                   B=ImpinjR2KFastSwitchInventory.ANTENNA2, Bloop=1,
                                                                   C=ImpinjR2KFastSwitchInventory.ANTENNA3, Cloop=1,
                                                                   D=ImpinjR2KFastSwitchInventory.ANTENNA4, Dloop=1,
                                                                   Interval=0,
                                                                   Repeat=1))
                continue

            try:

                self._logger.debug('Impinj RFID data: {}'.format(data))
                card_data = data
                card_data['time'] = OTime.now()

                # don't create new result if we already have fresh result for this tag (timeout, default 15s)
                card_id = data['epc']
                card_time = card_data['time']
                if card_id in self.timeout_list:
                    old_time = self.timeout_list[card_id]
                    if card_time - old_time < OTime(msec=self.timeout):
                        self._logger.debug('Duplicated result for tag {}, ignoring'.format(card_id))
                        continue

                self.timeout_list[card_id] = card_time

                self._queue.put(ImpinjCommand('card_data', card_data), timeout=1)

            except serial.serialutil.SerialException as e:
                self._logger.error(str(e))
                return
            except Exception as e:
                self._logger.error(str(e))

    def run_test(self):
        while True:
            if not main_thread().is_alive() or self._stop_event.is_set():
                self._logger.debug('Stop Impinj reader')
                return
            try:
                sleep(1)
                card_data = {}
                card_data['time'] = OTime.now()
                epc_list = ['00 00 00 01', '00 00 00 14', '00 00 00 0E', 'BFACACACACACACACACA']
                card_data['epc'] = epc_list[randint(0,3)]
                self._queue.put(ImpinjCommand('card_data', card_data), timeout=1)

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

        # self.timeout_list = {}
        # self.timeout = race().get_setting('readout_duplicate_timeout', 15000)  # timeout in milliseconds

    def run(self):
        time.sleep(1)
        while True:
            try:
                # time.sleep(0.1)
                # logging.debug('timeout = ' + str(self.timeout))
                # dummy_data = {'epc':'00 00 00 01', 'time':OTime.now()}
                # result = self._get_result(dummy_data)
                # # don't create new result if we already have fresh result for this tag (timeout 15s)
                # create_result= True
                # card_id = result.card_number
                # card_time = result.finish_time
                # if card_id in self.timeout_list:
                #     old_time = self.timeout_list[card_id]
                #     if card_time - old_time < OTime(msec=self.timeout):
                #         self._logger.debug('Duplicated result for tag {}, ignoring'.format(card_id))
                #         create_result = False
                # if create_result:
                #     self.timeout_list[card_id] = card_time
                #     self.data_sender.emit(result)

                cmd = self._queue.get(timeout=5)
                if cmd.command == 'card_data':
                    result = self._get_result(cmd.data)
                    self.data_sender.emit(result)

            except Empty:
                if not main_thread().is_alive() or self._stop_event.is_set():
                    break
            except Exception as e:
                self._logger.exception(e)
        self._logger.debug('Stop adder result')

    @staticmethod
    def _get_result(card_data):
        result = memory.race().new_result(memory.ResultRfidImpinj)

        limit = 10**8
        hex_offset = 5000000
        epc = str(card_data['epc']).replace(" ", "")

        # if epc contains only digits, use it directly
        # otherwise convert hex -> dec + add offset
        # 000014 = 14
        # 00000E = 5000014
        if epc.isdecimal():
            result.card_number = int(epc) % limit
        else:
            result.card_number = (int(epc, 16) + hex_offset) % limit

        result.finish_time = card_data['time']
        return result


@singleton
class ImpinjClient(object):
    def __init__(self):
        self._queue = Queue()
        self._stop_event = Event()
        self._impinj_thread = None
        self._result_thread = None
        self.port = None
        self._logger = logging.root
        self._call_back = None

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def _start_impinj_thread(self):
        if self._impinj_thread is None:
            self._impinj_thread = ImpinjThread(
                self.port,
                self._queue,
                self._stop_event,
                self._logger,
                debug=True
            )
            self._impinj_thread.start()
        elif self._impinj_thread.isFinished():
            self._impinj_thread= None
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
            return not self._impinj_thread.isFinished() and not self._result_thread.isFinished()

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
        return memory.race().get_setting('system_port', None)
