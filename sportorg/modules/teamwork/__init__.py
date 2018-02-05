from queue import Queue
from threading import Event, Thread, main_thread

from sportorg.core.singleton import singleton
from sportorg.models.memory import race
from sportorg.modules.teamwork.client import ClientThread, ClientCommand
from sportorg.modules.teamwork.server import ServerThread, ServerCommand


class ServerResultThread(Thread):
    def __init__(self, queue, logging=None):
        super().__init__()
        self._queue = queue
        self._logging = logging

    def run(self):
        while main_thread().is_alive():
            cmd = self._queue.get()
            print(cmd.data)


@singleton
class Server(object):
    def __init__(self):
        self._in_queue = Queue()
        self._out_queue = Queue()
        self._stop_event = Event()
        self._server_thread = None
        self._result_thread = None
        self.host = race().get_setting('teamwork_host', 'localhost')
        self.port = race().get_setting('teamwork_port', 50010)

    def _start_server_thread(self):
        if self._server_thread is None:
            self._server_thread = ServerThread(
                (self.host, self.port),
                self._in_queue,
                self._out_queue,
                self._stop_event
            )
            self._server_thread.start()
        elif not self._server_thread.is_alive():
            self._server_thread = None
            self._start_server_thread()

    def _start_result_thread(self):
        if self._result_thread is None:
            self._result_thread = ServerResultThread(
                self._out_queue
            )
            self._result_thread.start()
        elif not self._result_thread.is_alive():
            self._result_thread = None
            self._start_result_thread()

    def start(self):
        self._start_server_thread()
        self._start_result_thread()

    def send(self, data):
        self._in_queue.put(ServerCommand(data))


@singleton
class Client(object):
    def __init__(self):
        self._in_queue = Queue()
        self._out_queue = Queue()
        self._stop_event = Event()
        self._client_thread = None
        self.host = race().get_setting('teamwork_host', 'localhost')
        self.port = race().get_setting('teamwork_port', 50010)

    def _start_client_thread(self):
        if self._client_thread is None:
            self._client_thread = ClientThread(
                (self.host, self.port),
                self._in_queue,
                self._out_queue,
                self._stop_event
            )
            self._client_thread.start()
        elif not self._client_thread.is_alive():
            self._client_thread = None
            self._start_client_thread()

    def start(self):
        self._start_client_thread()

    def send(self, data):
        self._in_queue.put(ClientCommand(data))
