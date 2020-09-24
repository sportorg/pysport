import datetime
import logging
import time
from queue import Empty, Queue
from threading import Event, main_thread

from PySide2.QtCore import QThread, Signal

from sportorg.common.singleton import singleton
from sportorg.language import translate
from sportorg.libs.sfr import sfrreader
from sportorg.libs.sfr.sfrreader import SFRReaderCardChanged, SFRReaderException
from sportorg.models import memory
from sportorg.modules.sportident import backup
from sportorg.utils.time import time_to_otime


class SFRReaderCommand:
    def __init__(self, command, data=None):
        self.command = command
        self.data = data


class SFRReaderThread(QThread):

    POLL_TIMEOUT = 0.2

    def __init__(self, queue, stop_event, logger, debug=False):
        super().__init__()
        # self.setName(self.__class__.__name__)
        self.setObjectName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger
        self._debug = debug

    def run(self):
        try:
            sfr = sfrreader.SFRReaderReadout(logger=logging.root)
        except Exception as e:
            self._logger.error(str(e))
            return
        while True:
            try:
                while not sfr.poll_card():
                    time.sleep(self.POLL_TIMEOUT)
                    if not main_thread().is_alive() or self._stop_event.is_set():
                        sfr.disconnect()
                        self._logger.debug('Stop sfrreader')
                        return
                card_data = sfr.read_card()
                if sfr.is_card_connected():
                    self._queue.put(SFRReaderCommand('card_data', card_data), timeout=1)
                    sfr.ack_card()
            except SFRReaderException as e:
                self._logger.error(str(e))
            except SFRReaderCardChanged as e:
                self._logger.error(str(e))
            except Exception as e:
                self._logger.error(str(e))


class ResultThread(QThread):
    data_sender = Signal(object)

    def __init__(self, queue, stop_event, logger, start_time=None):
        super().__init__()
        # self.setName(self.__class__.__name__)
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
                if cmd.command == 'card_data':
                    result = self._get_result(self._check_data(cmd.data))
                    self.data_sender.emit(result)
                    backup.backup_data(cmd.data)
            except Empty:
                if not main_thread().is_alive() or self._stop_event.is_set():
                    break
            except Exception as e:
                self._logger.error(str(e))
        self._logger.debug('Stop adder result')

    def _check_data(self, card_data):
        return card_data

    @staticmethod
    def _get_result(card_data):
        result = memory.race().new_result(memory.ResultSFR)
        result.card_number = card_data['bib']  # SFR has no card id, only bib

        for i in range(len(card_data['punches'])):
            t = card_data['punches'][i][1]
            if t:
                split = memory.Split()
                split.code = str(card_data['punches'][i][0])
                split.time = time_to_otime(t)
                split.days = memory.race().get_days(t)
                if split.code != '0' and split.code != '':
                    result.splits.append(split)

        if card_data['start']:
            result.start_time = time_to_otime(card_data['start'])
        if card_data['finish']:
            result.finish_time = time_to_otime(card_data['finish'])

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
class SFRReaderClient(object):
    def __init__(self):
        self._queue = Queue()
        self._stop_event = Event()
        self._reader_thread = None
        self._result_thread = None
        self._logger = logging.root
        self._call_back = None

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def _start_reader_thread(self):
        if self._reader_thread is None:
            self._reader_thread = SFRReaderThread(
                self._queue, self._stop_event, self._logger, debug=True
            )
            self._reader_thread.start()
        # elif not self._reader_thread.is_alive():
        elif self._reader_thread.isFinished():
            self._reader_thread = None
            self._start_reader_thread()

    def _start_result_thread(self):
        if self._result_thread is None:
            self._result_thread = ResultThread(
                self._queue, self._stop_event, self._logger, self.get_start_time()
            )
            if self._call_back:
                self._result_thread.data_sender.connect(self._call_back)
            self._result_thread.start()
        # elif not self._result_thread.is_alive():
        elif self._result_thread.isFinished():
            self._result_thread = None
            self._start_result_thread()

    def is_alive(self):
        if self._reader_thread and self._result_thread:
            # return self._reader_thread.is_alive() and self._result_thread.is_alive()
            return (
                not self._reader_thread.isFinished()
                and not self._result_thread.isFinished()
            )

        return False

    def start(self):
        self._stop_event.clear()
        self._start_reader_thread()
        self._start_result_thread()

    def stop(self):
        self._stop_event.set()
        self._logger.info(translate('Closing connection'))

    def toggle(self):
        if self.is_alive():
            self.stop()
            return
        self.start()

    @staticmethod
    def get_start_time():
        start_time = memory.race().get_setting('system_zero_time', (8, 0, 0))
        return datetime.datetime.today().replace(
            hour=start_time[0],
            minute=start_time[1],
            second=start_time[2],
            microsecond=0,
        )
