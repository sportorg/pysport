import socket
from threading import Thread, main_thread
import json

import time


class ClientCommand:
    def __init__(self, data=None):
        self.data = data


class ClientSenderThread(Thread):
    def __init__(self, conn, in_queue, stop_event, logger=None):
        super().__init__()
        self.setName(self.__class__.__name__)
        self.conn = conn
        self._in_queue = in_queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        while True:
            try:
                while self._in_queue.empty():
                    if not main_thread().is_alive() or self._stop_event.is_set():
                        self.conn.close()
                        return
                    time.sleep(0.5)
                cmd = self._in_queue.get()
                data = json.dumps(cmd.data)
                self.conn.sendall(b'0' + data.encode() + b'1')
            except ConnectionResetError as e:
                print(str(e))
                break
            time.sleep(1)


class ClientReceiverThread(Thread):
    def __init__(self, conn, out_queue, stop_event, logger=None):
        super().__init__()
        self.setName(self.__class__.__name__)
        self.conn = conn
        self._out_queue = out_queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        full_data = b''
        while True:
            try:
                data = self.conn.recv(1024)
                if not data:
                    break
                full_data += data
                if data[-2:] == b'}1':
                    command = ClientCommand(json.loads(full_data[1:-1].decode()))
                    self._out_queue.put(command)  # for local
                    full_data = b''
            except ConnectionAbortedError as e:
                print(str(e))
                break
            except ConnectionResetError as e:
                print(str(e))
                break
            time.sleep(1)


class ClientThread(Thread):
    def __init__(self, addr, in_queue, out_queue, stop_event, logger=None):
        super().__init__()
        self.setName(self.__class__.__name__)
        self.addr = addr
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(self.addr)
                sender = ClientSenderThread(s, self._in_queue, self._stop_event, self._logger)
                sender.start()
                receiver = ClientReceiverThread(s, self._out_queue, self._stop_event, self._logger)
                receiver.start()

                sender.join()
                receiver.join()

            except ConnectionRefusedError as e:
                print(str(e))
                return

        s.close()


# in_q = Queue()
# out_q = Queue()
# ClientThread(('localhost', 50010), in_q, out_q, Event()).start()
#
# message = ''
# while message != 'q':
#     message = input()
#     in_q.put(ClientCommand({"message": message}))
