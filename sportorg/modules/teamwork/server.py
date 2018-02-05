import socket
from threading import Thread, main_thread
import json


class Connect:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self._alive = True

    def died(self):
        self._alive = False

    def is_alive(self):
        return self._alive


class ServerCommand:
    def __init__(self, data=None, addr=None):
        self.data = data
        self.addr = addr
        self.addr_exclude = []

    def exclude(self, addr):
        self.addr_exclude.append(addr)
        return self


class ServerReceiverThread(Thread):
    def __init__(self, conn, in_queue, out_queue, logger=None):
        super().__init__()
        # self.setName(self.__class__.__name__)
        self.connect = conn
        self._in_queue = in_queue
        self._out_queue = out_queue
        self.logger = logger

    def run(self):
        with self.connect.conn:
            print('Connected by', self.connect.addr)
            full_data = b''
            while True:
                try:
                    if not self.connect.is_alive():
                        break
                    data = self.connect.conn.recv(1024)
                    if not data:
                        break
                    full_data += data
                    if data[-2:] == b'}1':
                        command = ServerCommand(json.loads(full_data[1:-1].decode()), self.connect.addr)
                        command.exclude(self.connect.addr)
                        self._out_queue.put(command)  # for local
                        self._in_queue.put(command)  # for child
                        full_data = b''
                except ConnectionResetError as e:
                    print(str(e))
                    break
        self.connect.conn.close()


class ServerSenderThread(Thread):
    def __init__(self, in_queue, logger=None):
        super().__init__()
        # self.setName(self.__class__.__name__)
        self.connections = []
        self._in_queue = in_queue
        self.logger = logger

    def append(self, conn_object):
        self.connections.append(conn_object)

    def run(self):
        while True:
            try:
                while self._in_queue.empty():
                    if not main_thread().is_alive():
                        break
                command = self._in_queue.get()
                for connect in self.connections:
                    try:
                        if connect.addr not in command.addr_exclude and connect.is_alive():
                            data = json.dumps(command.data)
                            connect.conn.sendall(b'0' + data.encode() + b'1')
                    except ConnectionResetError as e:
                        print(str(e))
                        connect.died()
                    except OSError as e:
                        print(str(e))
                        connect.died()
            except Exception as e:
                print(str(e))


class ServerThread(Thread):
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
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                s.bind(self.addr)
            except Exception as e:
                print(str(e))
                return
            s.listen(1)
            sender = ServerSenderThread(self._in_queue, self._logger)
            sender.start()

            while True:
                conn, addr = s.accept()
                connect = Connect(conn, addr)
                sender.append(connect)
                try:
                    ServerReceiverThread(connect, self._in_queue, self._out_queue, self._logger).start()
                except Exception as e:
                    print(str(e))


# in_q = Queue()
# out_q = Queue()
# server = ServerThread(('', 50010), in_q, out_q, None)
# server.start()
#
# while True:
#     while out_q.empty():
#         if not server.is_alive():
#             exit(0)
#     cmd = out_q.get()
#     print(cmd.data, cmd.addr)

