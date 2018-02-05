from queue import Queue
from threading import Event

from sportorg.core.singleton import singleton
from sportorg.modules.teamwork.client import ClientThread, ClientCommand
from sportorg.modules.teamwork.server import ServerThread, ServerCommand


@singleton
class Server(object):
    def __init__(self):
        self._in_queue = Queue()
        self._out_queue = Queue()
        self._stop_event = Event()
        self._server_thread = None
        self.host = ''
        self.port = 50010

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

    def start(self):
        self._start_server_thread()

    def send(self, data):
        self._start_server_thread()
        self._in_queue.put(ServerCommand(data))


@singleton
class Client(object):
    def __init__(self):
        self._in_queue = Queue()
        self._out_queue = Queue()
        self._stop_event = Event()
        self._client_thread = None
        self.host = 'localhost'
        self.port = 50010

    def _start_client_thread(self):
        if self._server_thread is None:
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
        self._start_client_thread()
        self._in_queue.put(ClientCommand(data))
