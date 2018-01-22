import datetime
import logging
from queue import Queue
from threading import main_thread, Event

import time

import serial
from PyQt5.QtCore import QThread

from sportorg.core.singleton import Singleton
from sportorg.language import _
from sportorg.gui.global_access import GlobalAccess
from sportorg.libs.sportident import sireader
from sportorg.models import memory
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.modules.live.orgeo import OrgeoClient
from sportorg.modules.printing.model import split_printout, NoResultToPrintException, NoPrinterSelectedException
from sportorg.modules.sportident import backup
from sportorg.modules.sportident.result_generation import ResultSportidentGeneration
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
            si = sireader.SIReaderReadout(port=self.port, debug=self._debug)
        except Exception as e:
            self._logger.exception(str(e))
            return
        while True:
            try:
                while not si.poll_sicard():
                    time.sleep(0.5)
                    if not main_thread().is_alive() or self._stop_event.is_set():
                        si.disconnect()
                        self._logger.debug('Stop sireader')
                        return
                card_data = si.read_sicard()
                card_data['card_type'] = si.cardtype
                self._queue.put(SIReaderCommand('card_data', card_data), timeout=1)
                si.ack_sicard()
            except sireader.SIReaderException as e:
                self._logger.debug(str(e))
            except sireader.SIReaderCardChanged as e:
                self._logger.debug(str(e))
            except serial.serialutil.SerialException as e:
                self._logger.debug(str(e))
                return
            except Exception as e:
                self._logger.exception(str(e))


class ResultThread(QThread):
    def __init__(self, queue, stop_event, logger, start_time=None):
        super().__init__()
        # self.setName(self.__class__.__name__)
        self.setObjectName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger
        self.start_time = start_time

    def run(self):
        time.sleep(5)
        while True:
            try:
                while True:
                    if not main_thread().is_alive() or self._stop_event.is_set():
                        self._logger.debug('Stop adder result')
                        return
                    if not self._queue.empty():
                        break
                    time.sleep(0.5)

                cmd = self._queue.get()
                if cmd.command == 'card_data':
                    assignment_mode = memory.race().get_setting('sportident_assignment_mode', False)
                    if not assignment_mode:
                        result = self._get_result(self._check_data(cmd.data))
                        GlobalAccess().clear_filters(remove_condition=False)
                        ResultSportidentGeneration(result).add_result()
                        ResultCalculation().process_results()
                        if memory.race().get_setting('split_printout', False):
                            try:
                                split_printout(result)
                            except NoResultToPrintException as e:
                                logging.error(str(e))
                            except NoPrinterSelectedException as e:
                                logging.error(str(e))
                            except Exception as e:
                                logging.exception(str(e))
                        GlobalAccess().auto_save()
                        backup.backup_data(cmd.data)
                        OrgeoClient().send_results()
                    # GlobalAccess().get_main_window().init_model()
            except Exception as e:
                self._logger.exception(str(e))

    def _check_data(self, card_data):
        if self.start_time is not None and card_data['card_type'] == 'SI5':
            start_time = self.time_to_sec(self.start_time)
            for i in range(len(card_data['punches'])):
                if self.time_to_sec(card_data['punches'][i][1]) < start_time:
                    new_datetime = card_data['punches'][i][1].replace(hour=card_data['punches'][i][1].hour+12)
                    card_data['punches'][i] = (card_data['punches'][i][0], new_datetime)

        return card_data

    @staticmethod
    def _get_result(card_data):
        result = memory.ResultSportident()
        result.sportident_card = memory.race().new_sportident_card(card_data['card_number'])

        for i in range(len(card_data['punches'])):
            t = card_data['punches'][i][1]
            if t:
                split = memory.Split()
                split.code = card_data['punches'][i][0]
                split.time = time_to_otime(t)
                result.splits.append(split)

        if card_data['start']:
            result.start_time = time_to_otime(card_data['start'])
        if card_data['finish']:
            result.finish_time = time_to_otime(card_data['finish'])

        return result

    @staticmethod
    def time_to_sec(value, max_val=86400):
        if isinstance(value, datetime.datetime):
            ret = value.hour * 3600 + value.minute * 60 + value.second + value.microsecond / 1000000
            if max_val:
                ret = ret % max_val
            return ret

        return 0


class SIReaderClient(metaclass=Singleton):
    def __init__(self):
        self._queue = Queue()
        self._stop_event = Event()
        self._si_reader_thread = None
        self._result_thread = None
        self.port = None
        self._logger = logging.root

        start_time = memory.race().get_setting('sportident_zero_time', (8, 0, 0))
        self._start_time = datetime.datetime.today().replace(
            hour=start_time[0],
            minute=start_time[1],
            second=start_time[2],
            microsecond=0
        )

    def _start_si_reader_thread(self):
        if self._si_reader_thread is None:
            self._si_reader_thread = SIReaderThread(
                self.port,
                self._queue,
                self._stop_event,
                self._logger
            )
            self._si_reader_thread.start()
        # elif not self._si_reader_thread.is_alive():
        elif self._si_reader_thread.isFinished():
            self._si_reader_thread = None
            self._start_si_reader_thread()

    def _start_result_thread(self):
        if self._result_thread is None:
            self._result_thread = ResultThread(
                self._queue,
                self._stop_event,
                self._logger,
                self._start_time
            )
            self._result_thread.start()
        # elif not self._result_thread.is_alive():
        elif self._result_thread.isFinished():
            self._result_thread = None
            self._start_result_thread()

    def is_alive(self):
        if self._si_reader_thread is not None and self._result_thread is not None:
            # return self._si_reader_thread.is_alive() and self._result_thread.is_alive()
            return not self._si_reader_thread.isFinished() and not self._result_thread.isFinished()

        return False

    def start(self):
        if self.is_alive():
            self.stop()
            return
        self.port = self.choose_port()
        if self.port:
            self._stop_event.clear()
            self._start_si_reader_thread()
            self._start_result_thread()
            self._logger.info(_('Opening port') + ' ' + self.port)
        else:
            self._logger.info(_('Cannot open port'))
            self._logger.info(_('SPORTident readout activated'))

    def stop(self):
        self._stop_event.set()
        self._logger.info(_('Closing port'))

    @staticmethod
    def get_ports():
        ports = []
        for i in range(32):
            try:
                p = 'COM' + str(i)
                com = serial.Serial(p, 38400, timeout=5)
                com.close()
                ports.append(p)
            except serial.SerialException:
                continue

        return ports

    def choose_port(self):
        ports = self.get_ports()
        if len(ports):
            self._logger.debug('Available Ports')
            for i, p in enumerate(ports):
                self._logger.debug("{} - {}".format(i, p))
            return ports[0]
        else:
            self._logger.debug("No ports available")
            return None
