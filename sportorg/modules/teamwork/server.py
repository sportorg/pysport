import socket
from queue import Empty, Queue
from threading import Event, Thread, main_thread

import orjson

from .packet_header import Header, ObjectTypes, Operations


class Command:
    def __init__(self, data=None, op=Operations.Update.name, addr=None):
        self.data = data
        self.addr = addr
        self.header = Header(data, op)
        self.addr_exclude = []
        self.next_cmd_obj_type = ObjectTypes.Unknown.value

    def __repr__(self) -> str:
        return str(self.data)

    def exclude(self, addr):
        self.addr_exclude.append(addr)
        return self

    def get_packet(self):
        pack_data = orjson.dumps(self.data)
        return self.header.pack_header(len(pack_data)) + pack_data


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
    def __init__(self, conn, in_queue, out_queue, stop_event, logger):
        super().__init__(daemon=True)
        self.connect = conn
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        with self.connect.conn:
            self._logger.debug('Server receiver started')
            self._logger.info('Connected by {}'.format(self.connect.addr))
            full_data = b''
            self.connect.conn.settimeout(5)
            hdr = Header()
            is_new_pack = True
            while True:
                try:
                    data = self.connect.conn.recv(1024)
                    if not data:
                        break
                    full_data += data
                    while True:
                        # getting Header
                        if is_new_pack:
                            if len(full_data) >= hdr.header_size:
                                hdr.unpack_header(full_data[: hdr.header_size])
                                full_data = full_data[hdr.header_size :]
                                is_new_pack = False
                            else:
                                break
                        # Getting JSON data
                        else:
                            if len(full_data) >= hdr.size:
                                command = Command(
                                    orjson.loads(full_data[: hdr.size].decode()),
                                    Operations(hdr.op_type).name,
                                    self.connect.addr,
                                )
                                command.exclude(self.connect.addr)
                                self._out_queue.put(command)  # for local
                                self._in_queue.put(command)  # for child
                                full_data = full_data[hdr.size :]
                                is_new_pack = True
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
    def __init__(self, in_queue, connections_queue, stop_event, logger):
        super().__init__(daemon=True)
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
                        if (
                            connect.addr not in command.addr_exclude
                            and connect.is_alive()
                        ):
                            connect.conn.sendall(command.get_packet())
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
    def __init__(self, addr, in_queue, out_queue, stop_event, logger):
        super().__init__(daemon=True)
        self.setName(self.__class__.__name__)
        self.addr = addr
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._stop_event = stop_event
        self._logger = logger
        self._server_started = Event()

    def join_server(self) -> None:
        self._server_started.wait()

    def run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                s.bind(self.addr)
            except Exception as e:
                self._logger.debug(str(e))
                return
            s.listen(1)
            s.settimeout(5)

            self._logger.info('Server started')

            conns_queue = Queue()  # type: ignore
            sender = ServerSenderThread(
                self._in_queue, conns_queue, self._stop_event, self._logger
            )
            sender.start()
            self._server_started.set()

            connections = []

            while True:
                try:
                    conn, addr = s.accept()
                    connect = Connect(conn, addr)
                    conns_queue.put(connect)
                    srt = ServerReceiverThread(
                        connect,
                        self._in_queue,
                        self._out_queue,
                        self._stop_event,
                        self._logger,
                    )
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
            self._logger.info('Server stopped')
