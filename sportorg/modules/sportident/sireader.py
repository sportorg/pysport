import datetime
import logging
import os
import platform
import re
import time
from queue import Empty, Queue
from threading import Event, main_thread

import serial
from PySide2.QtCore import QThread, Signal
from sportident import (
    SIReader,
    SIReaderCardChanged,
    SIReaderControl,
    SIReaderException,
    SIReaderReadout,
    SIReaderSRR,
)

from sportorg.common.singleton import singleton
from sportorg.language import translate
from sportorg.models import memory
from sportorg.modules.sportident import backup
from sportorg.utils.time import time_to_otime


class SIReaderCommand:
    def __init__(self, command, data=None):
        self.command = command
        self.data = data


class SIReaderThread(QThread):
    def __init__(self, port, queue, stop_event, logger, debug=False):
        self.port = port
        super().__init__()
        # self.setName(self.__class__.__name__)
        self.setObjectName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger
        self._debug = debug

    def run(self):
        try:
            si = SIReaderReadout(port=self.port, logger=logging.root)
            if si.get_type() == SIReader.M_SRR:
                si.disconnect()  # release port
                si = SIReaderSRR(port=self.port, logger=logging.root)
            elif (
                si.get_type() == SIReader.M_CONTROL
                or si.get_type() == SIReader.M_BC_CONTROL
            ):
                si.disconnect()  # release port
                si = SIReaderControl(port=self.port, logger=logging.root)

            si.poll_sicard()  # try to poll immediately to catch an exception
        except Exception as e:
            self._logger.debug(str(e))
            return

        max_error = 2000
        error_count = 0

        while True:
            try:
                while not si.poll_sicard():
                    time.sleep(0.2)
                    if not main_thread().is_alive() or self._stop_event.is_set():
                        si.disconnect()
                        self._logger.debug('Stop sireader')
                        return
                card_data = si.read_sicard()
                card_data['card_type'] = si.cardtype
                self._queue.put(SIReaderCommand('card_data', card_data), timeout=1)
                si.ack_sicard()
            except SIReaderException as e:
                error_count += 1
                self._logger.error(str(e))
                if error_count > max_error:
                    return
            except SIReaderCardChanged as e:
                self._logger.error(str(e))
            except serial.serialutil.SerialException as e:
                self._logger.error(str(e))
                return
            except Exception as e:
                self._logger.exception(str(e))


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
        # TODO requires more complex checking for long starts > 12 hours
        if self.start_time and card_data['card_type'] == 'SI5':
            start_time = self.time_to_sec(self.start_time)
            for i in range(len(card_data['punches'])):
                if self.time_to_sec(card_data['punches'][i][1]) < start_time:
                    new_datetime = card_data['punches'][i][1].replace(
                        hour=(card_data['punches'][i][1].hour + 12) % 24
                    )
                    card_data['punches'][i] = (card_data['punches'][i][0], new_datetime)

                # simple check for morning starts (10:00 a.m. was 22:00 in splits)
                if (
                    self.time_to_sec(card_data['punches'][i][1]) - 12 * 3600
                    > start_time
                ):
                    new_datetime = card_data['punches'][i][1].replace(
                        hour=card_data['punches'][i][1].hour - 12
                    )
                    card_data['punches'][i] = (card_data['punches'][i][0], new_datetime)

        return card_data

    @staticmethod
    def _get_result(card_data):
        result = memory.race().new_result()
        result.card_number = int(card_data['card_number'])

        for i in range(len(card_data['punches'])):
            t = card_data['punches'][i][1]
            if t:
                split = memory.Split()
                split.code = str(card_data['punches'][i][0])
                split.time = time_to_otime(t)
                split.days = memory.race().get_days(t)
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
class SIReaderClient(object):
    def __init__(self):
        self._queue = Queue()
        self._stop_event = Event()
        self._si_reader_thread = None
        self._result_thread = None
        self.port = None
        self._logger = logging.root
        self._call_back = None

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def _start_si_reader_thread(self):
        if self._si_reader_thread is None:
            self._si_reader_thread = SIReaderThread(
                self.port, self._queue, self._stop_event, self._logger, debug=True
            )
            self._si_reader_thread.start()
        # elif not self._si_reader_thread.is_alive():
        elif self._si_reader_thread.isFinished():
            self._si_reader_thread = None
            self._start_si_reader_thread()

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
        if self._si_reader_thread and self._result_thread:
            # return self._si_reader_thread.is_alive() and self._result_thread.is_alive()
            return (
                not self._si_reader_thread.isFinished()
                and not self._result_thread.isFinished()
            )

        return False

    def start(self):
        self.port = self.choose_port()
        if self.port:
            self._stop_event.clear()
            self._start_si_reader_thread()
            self._start_result_thread()
            self._logger.info(translate('Opening port') + ' ' + self.port)
        else:
            self._logger.info(translate('Cannot open port'))

    def stop(self):
        self._stop_event.set()
        self._logger.info(translate('Closing port'))

    def toggle(self):
        if self.is_alive():
            self.stop()
            return
        self.start()

    @staticmethod
    def get_ports():
        ports = []
        if platform.system() == 'Linux':
            scan_ports = [
                os.path.join('/dev', f)
                for f in os.listdir('/dev')
                if re.match('ttyS.*|ttyUSB.*', f)
            ]
        elif platform.system() == 'Windows':
            scan_ports = ['COM' + str(i) for i in range(48)]

        for p in scan_ports:
            try:
                com = serial.Serial(p, 38400, timeout=5)
                com.close()
                ports.append(p)
            except serial.SerialException:
                continue

        return ports

    def choose_port(self):
        si_port = memory.race().get_setting('system_port', '')
        if si_port:
            return si_port
        ports = self.get_ports()
        if len(ports):
            self._logger.info(translate('Available Ports'))
            for i, p in enumerate(ports):
                self._logger.info('{} - {}'.format(i, p))
            return ports[0]
        else:
            self._logger.info('No ports available')
            return None

    @staticmethod
    def get_start_time():
        start_time = memory.race().get_setting('system_zero_time', (8, 0, 0))
        return datetime.datetime.today().replace(
            hour=start_time[0],
            minute=start_time[1],
            second=start_time[2],
            microsecond=0,
        )
