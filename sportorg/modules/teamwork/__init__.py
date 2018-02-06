import logging
from queue import Queue
from threading import Event, main_thread

import time
from PyQt5.QtCore import QThread

from sportorg.core.singleton import singleton
from sportorg.models.memory import race
from sportorg.modules.teamwork.client import ClientThread
from sportorg.modules.teamwork.server import ServerThread, Command


class ResultThread(QThread):
    def __init__(self, queue, stop_event, logger=None):
        super().__init__()
        # self.setName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        while True:
            cmd = self._queue.get()
            self._logger.debug(repr(cmd.data))


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

    def _start_thread(self):
        host = race().get_setting('teamwork_host', 'localhost')
        port = race().get_setting('teamwork_port', 50010)
        connection_type = race().get_setting('teamwork_type_connection', 'client')

        if connection_type not in self.factory.keys():
            return
        if self._thread is None:
            self._thread = self.factory[connection_type](
                (host, port),
                self._in_queue,
                self._out_queue,
                self._stop_event,
                logging.root
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
                logging.root
            )
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

    def send(self, data):
        if self.is_alive():
            self._in_queue.put(Command(data))
