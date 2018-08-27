import logging
from queue import Queue, Empty
from threading import Event, main_thread

from PyQt5.QtCore import QThread, pyqtSignal

from sportorg.core.broker import Broker
from sportorg.core.singleton import singleton
from .client import ClientThread
from .server import ServerThread, Command


class ResultThread(QThread):
    data_sender = pyqtSignal(object)

    def __init__(self, queue, stop_event, logger=None):
        super().__init__()
        # self.setName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        self._logger.debug('Teamwork result start')
        while True:
            try:
                cmd = self._queue.get(timeout=5)
                self.data_sender.emit(cmd)
            except Empty:
                if not main_thread().is_alive() or self._stop_event.is_set():
                    break
            except Exception as e:
                self._logger.debug(str(e))
        self._logger.debug('Teamwork result shutdown')


@singleton
class Teamwork(object):
    def __init__(self):
        self._in_queue = Queue()
        self._out_queue = Queue()
        self._stop_event = Event()
        self.factory = {
            'client': ClientThread,
            'server': ServerThread
        }
        self._thread = None
        self._result_thread = None
        self._call_back = None
        self._logger = logging.root

        self.host = ''
        self.port = 50010
        self.token = ''
        self.connection_type = 'client'

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def set_options(self, host, port, token, connection_type):
        self.host = host
        self.port = port
        self.token = token
        self.connection_type = connection_type

    def _start_thread(self):
        if self.connection_type not in self.factory.keys():
            return
        if self._thread is None:
            self._thread = self.factory[self.connection_type](
                (self.host, self.port),
                self._in_queue,
                self._out_queue,
                self._stop_event,
                self._logger
            )
            self._thread.start()
        elif not self._thread.is_alive():
            self._thread = None
            self._start_thread()

    def _start_result_thread(self):
        if self._result_thread is None:
            self._result_thread = ResultThread(
                self._out_queue,
                self._stop_event,
                self._logger
            )
            if self._call_back is not None:
                self._result_thread.data_sender.connect(self._call_back)
            self._result_thread.start()
        # elif not self._result_thread.is_alive():
        elif self._result_thread.isFinished():
            self._result_thread = None
            self._start_result_thread()

    def is_alive(self):
        return self._thread is not None and self._thread.is_alive() \
               and self._result_thread is not None and not self._result_thread.isFinished()

    def stop(self):
        self._stop_event.set()

    def start(self):
        self._stop_event.clear()
        self._in_queue.queue.clear()
        self._out_queue.queue.clear()

        self._start_thread()
        self._start_result_thread()

    def toggle(self):
        if self.is_alive():
            self.stop()
            self._logger.info('{} stopping'.format(self.connection_type.upper()))
        else:
            self.start()
            self._logger.info('{} starting'.format(self.connection_type.upper()))

    def send(self, data):
        """data is Dict or List[Dict]"""
        Broker().produce('teamwork_sending', data)
        if self.is_alive():
            if isinstance(data, list):
                for item in data:
                    self._in_queue.put(Command(item))
                return

            self._in_queue.put(Command(data))

    def delete(self, data):
        """data is Dict or List[Dict]"""
        Broker().produce('teamwork_deleting', data)
        if self.is_alive():
            pass
