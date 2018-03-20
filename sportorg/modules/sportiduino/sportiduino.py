import datetime
import logging
from queue import Queue, Empty
from threading import main_thread, Event

import time

from PyQt5.QtCore import QThread, pyqtSignal

from sportorg.core.singleton import singleton
from sportorg.language import _
from sportorg.libs.sportiduino import sportiduino
from sportorg.models import memory
from sportorg.utils.time import time_to_otime


class SportiduinoCommand:
    def __init__(self, command, data=None):
        self.command = command
        self.data = data


class SportiduinoThread(QThread):
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
            sduino = sportiduino.Sportiduino(port=self.port)
        except Exception as e:
            self._logger.error(str(e))
            return

        while True:
            try:
                while not sduino.poll_card():
                    time.sleep(0.5)
                    if not main_thread().is_alive() or self._stop_event.is_set():
                        sduino.disconnect()
                        self._logger.debug('Stop sportiduino reader')
                        return
                card_data = sduino.card_data
                self._queue.put(SportiduinoCommand('card_data', card_data), timeout=1)
                sduino.beep_ok()
            except sduino.SportiduinoException as e:
                self._logger.error(str(e))
            except serial.serialutil.SerialException as e:
                self._logger.error(str(e))
                return
            except Exception as e:
                self._logger.error(str(e))


class ResultThread(QThread):
    data_sender = pyqtSignal(object)

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
                if cmd.command == 'card_data':
                    result = self._get_result(cmd.data)
                    self.data_sender.emit(result)
            except Empty:
                if not main_thread().is_alive() or self._stop_event.is_set():
                    break
            except Exception as e:
                self._logger.error(str(e))
        self._logger.debug('Stop adder result')

    @staticmethod
    def _get_result(card_data):
        result = memory.race().new_sportident_result()
        result.sportident_card = int(card_data['card_number'])

        for i in range(len(card_data['punches'])):
            t = card_data['punches'][i][1]
            if t:
                split = memory.Split()
                split.code = card_data['punches'][i][0]
                split.time = time_to_otime(t)
                split.days = memory.race().get_days(t)
                result.splits.append(split)

        if card_data['start']:
            result.start_time = time_to_otime(card_data['start'])
        if card_data['finish']:
            result.finish_time = time_to_otime(card_data['finish'])

        return result

    @staticmethod
    def time_to_sec(value):
        if isinstance(value, datetime.datetime):
            ret = value.hour * 3600 + value.minute * 60 + value.second + value.microsecond / 1000000
            return ret

        return 0


@singleton
class SportiduinoClient(object):
    def __init__(self):
        self._queue = Queue()
        self._stop_event = Event()
        self._sportiduino_thread = None
        self._result_thread = None
        self.port = None
        self._logger = logging.root
        self._call_back = None

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def _start_sportiduino_thread(self):
        if self._sportiduino_thread is None:
            self._sportiduino_thread = SportiduinoThread(
                self.port,
                self._queue,
                self._stop_event,
                self._logger,
                debug=True
            )
            self._sportiduino_thread.start()
        elif self._sportiduino_thread.isFinished():
            self._sportiduino_thread= None
            self._start_sportiduino_thread()

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
        if self._sportiduino_thread is not None and self._result_thread is not None:
            return not self._sportiduino_thread.isFinished() and not self._result_thread.isFinished()

        return False

    def start(self):
        self.port = self.choose_port()
        self._stop_event.clear()
        self._start_sportiduino_thread()
        self._start_result_thread()

    def stop(self):
        self._stop_event.set()

    def toggle(self):
        if self.is_alive():
            self.stop()
            return
        self.start()

    def choose_port(self):
        return memory.race().get_setting('sportident_port', '')

