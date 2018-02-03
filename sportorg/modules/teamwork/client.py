import socket
from threading import Thread, Event, main_thread
from queue import Queue
import json

import time


class ClientCommand:
    def __init__(self, data=None):
        self.data = data


class ClientThread(Thread):
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
            try:
                s.connect((self.host, self.port))
            except ConnectionRefusedError:
                return
            while True:
                try:
                    while True:
                        if not main_thread().is_alive() or self._stop_event.is_set():
                            s.close()
                            return
                        if not self._queue.empty():
                            break
                        time.sleep(0.5)
                    cmd = self._queue.get()
                    data = json.dumps(cmd.data)
                    s.sendall(b'0' + data.encode() + b'1')
                    ret = s.recv(1024)
                    print(ret.decode())
                except ConnectionResetError:
                    break
                time.sleep(1)
        s.close()


q = Queue()
ClientThread('localhost', 50010, q, Event()).start()

for i in range(10):
    q.put(ClientCommand({"hello": True}))
    time.sleep(1)
