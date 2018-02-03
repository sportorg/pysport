import socket
from threading import Thread, Event, main_thread
from queue import Queue
import json

import time

from sportorg.core.singleton import singleton


class ServerCommand:
    def __init__(self, data=None):
        self.data = data


class ServerThread(Thread):
    def __init__(self, host, port, queue, stop_event, logger=None):
        super().__init__()
        self.setName(self.__class__.__name__)
        self.host = host
        self.port = port
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen(1)
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                full_data = b''
                while True:
                    try:
                        data = conn.recv(1024)
                        if not data:
                            break
                        full_data += data
                        if data[-2:] == b'}1':
                            self._queue.put(ServerCommand(json.loads(full_data[1:-1].decode())))
                            full_data = b''
                            conn.sendall(b'Ok')
                    except ConnectionResetError:
                        break
            s.close()


q = Queue()
server = ServerThread('', 50010, q, None)
server.start()

while True:
    while q.empty():
        if not server.is_alive():
            exit(0)
    cmd = q.get()
    print(cmd.data)


# @singleton
# class Server(object):
#     def __init__(self):
#         self._queue = Queue()
#         self._stop_event = Event()
#         self._server_thread = None
#         self.host = ''
#         self.port = 50010
#
#     def _start_server_thread(self):
#         if self._server_thread is None:
#             self._server_thread = ServerThread(
#                 self.host,
#                 self.port,
#                 self._queue,
#                 self._stop_event
#             )
#             self._server_thread.start()
#         elif not self._server_thread.is_alive():
#             self._server_thread = None
#             self._start_server_thread()
