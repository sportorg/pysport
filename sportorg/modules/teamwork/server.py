import socket
from queue import Queue, Empty
from threading import Thread, Event, main_thread
import json


class Command:
    def __init__(self, data=None, addr=None):
        self.data = data
        self.addr = addr
        self.addr_exclude = []

    def exclude(self, addr):
        self.addr_exclude.append(addr)
        return self


class Connect:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self._alive = Event()

    def died(self):
        self._alive.set()

    def is_alive(self):
        return not self._alive.is_set()


class ServerReceiverThread(Thread):
    def __init__(self, conn, in_queue, out_queue, stop_event, logger=None):
        super().__init__()
        # self.setName(self.__class__.__name__)
        self.connect = conn
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        with self.connect.conn:
            self._logger.debug('Server receiver start')
            self._logger.info('Connected by {}'.format(self.connect.addr))
            full_data = b''
            self.connect.conn.settimeout(5)
            while True:
                try:
                    data = self.connect.conn.recv(1024)
                    if not data:
                        break
                    full_data += data
                    while True:
                        offset = 0
                        while True:
                            try:
                                json.loads(full_data[:offset].decode())
                                break
                            except ValueError:
                                if offset >= len(full_data):
                                    offset = -1
                                    break
                                offset += 1
                        if offset != -1:
                            command = Command(json.loads(full_data[:offset].decode()), self.connect.addr)
                            command.exclude(self.connect.addr)
                            self._out_queue.put(command)  # for local
                            self._in_queue.put(command)  # for child
                            full_data = full_data[offset:]
                        else:
                            break
                except socket.timeout:
                    if not main_thread().is_alive() or self._stop_event.is_set():
                        break
                except ConnectionResetError as e:
                    self._logger.error(str(e))
                    break
                except Exception as e:
                    self._logger.error(str(e))
                    break
        self.connect.conn.close()
        self.connect.died()
        self._logger.info('Disconnect {}'.format(self.connect.addr))


class ServerSenderThread(Thread):
    def __init__(self, in_queue, connections_queue, stop_event, logger=None):
        super().__init__()
        self.setName(self.__class__.__name__)
        self._connections_queue = connections_queue
        self._connections = []
        self._in_queue = in_queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        self._logger.debug('Server sender start')
        while True:
            try:
                command = self._in_queue.get(timeout=5)
                for connect in self._connections:
                    try:
                        if connect.addr not in command.addr_exclude and connect.is_alive():
                            data = json.dumps(command.data)
                            connect.conn.sendall(data.encode())
                    except ConnectionResetError as e:
                        self._logger.error(str(e))
                        connect.died()
                    except OSError as e:
                        self._logger.error(str(e))
                        connect.died()
            except Empty:
                while not self._connections_queue.empty():
                    self._connections.append(self._connections_queue.get())
                if not main_thread().is_alive() or self._stop_event.is_set():
                    break
            except Exception as e:
                self._logger.error(str(e))
        self._logger.debug('Server sender shutdown')
        self._stop_event.set()


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
                self._logger.debug(str(e))
                return
            s.listen(1)
            s.settimeout(5)

            self._logger.info('Server start')

            conns_queue = Queue()
            sender = ServerSenderThread(self._in_queue, conns_queue, self._stop_event, self._logger)
            sender.start()

            connections = []

            while True:
                try:
                    conn, addr = s.accept()
                    connect = Connect(conn, addr)
                    conns_queue.put(connect)
                    srt = ServerReceiverThread(connect, self._in_queue, self._out_queue, self._stop_event, self._logger)
                    srt.start()
                    connections.append(srt)
                except socket.timeout:
                    if not main_thread().is_alive() or self._stop_event.is_set():
                        break
                except Exception as e:
                    self._logger.error(str(e))
            sender.join()
            for srt in connections:
                srt.join()
            self._logger.info('Server shutdown')
