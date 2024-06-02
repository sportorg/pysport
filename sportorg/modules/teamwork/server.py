import selectors
import socket
from queue import Empty, Queue
from threading import Event, Thread
from typing import List, Tuple, cast

import orjson

from .command import Command
from .packet_header import Header, Operations


class ServerReceiver:
    MSG_SIZE = 1024

    def __init__(
        self,
        selector: selectors.BaseSelector,
        in_queue: Queue,
        out_queue: Queue,
        logger,
    ):
        self._selector = selector
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._logger = logger
        self._full_data = b''
        self._hdr = Header()
        self._is_new_pack = True

    def __call__(self, sock: socket.socket) -> None:
        try:
            data = sock.recv(self.MSG_SIZE)
            if not data:
                self._selector.unregister(sock)
                sock.close()
                return
        except OSError as e:
            self._logger.error(str(e))
            self._selector.unregister(sock)
            sock.close()
            return
        try:
            self._full_data += data
            while True:
                # getting Header
                if self._is_new_pack:
                    if len(self._full_data) >= self._hdr.header_size:
                        self._hdr.unpack_header(
                            self._full_data[: self._hdr.header_size]
                        )
                        self._full_data = self._full_data[self._hdr.header_size :]
                        self._is_new_pack = False
                    else:
                        break
                # Getting JSON data
                else:
                    if len(self._full_data) >= self._hdr.size:
                        command = Command(
                            orjson.loads(self._full_data[: self._hdr.size].decode()),
                            Operations(self._hdr.op_type).name,
                            sender=sock,
                        )
                        self._out_queue.put(command)  # for local
                        self._in_queue.put(command)  # for child
                        self._full_data = self._full_data[self._hdr.size :]
                        self._is_new_pack = True
                    else:
                        break
        except Exception as e:
            self._logger.error(str(e))


class ServerSender:
    def __init__(self, selector: selectors.BaseSelector, in_queue: Queue, logger):
        self._selector = selector
        self._in_queue = in_queue
        self._logger = logger

    def __call__(self, socks: List[socket.socket]) -> None:
        try:
            while True:
                command = self._in_queue.get(timeout=0.1)
                for sock in socks:
                    if command.is_sender(sock):
                        continue
                    try:
                        sock.sendall(command.get_packet())
                    except OSError as e:
                        self._logger.error(str(e))
                        self._selector.unregister(sock)
                        sock.close()
        except Empty:
            pass


class ConnectionAcceptor:
    def __init__(
        self,
        selector: selectors.BaseSelector,
        in_queue: Queue,
        out_queue: Queue,
        logger,
    ):
        self._selector = selector
        self._logger = logger
        self._in_queue = in_queue
        self._out_queue = out_queue

    def __call__(self, sock: socket.socket) -> None:
        conn, addr = sock.accept()
        self._selector.register(
            conn,
            selectors.EVENT_READ | selectors.EVENT_WRITE,
            data=ServerReceiver(
                self._selector, self._in_queue, self._out_queue, self._logger
            ),
        )


class ServerThread(Thread):
    def __init__(
        self,
        addr: Tuple[str, int],
        in_queue: Queue,
        out_queue: Queue,
        stop_event: Event,
        logger,
    ):
        super().__init__(daemon=True)
        self.setName('Teamwork Server')
        self.addr = addr
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._stop_event = stop_event
        self._logger = logger
        self._started = Event()

    def wait(self) -> None:
        self._started.wait()

    def run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                s.bind(self.addr)
            except Exception as e:
                self._logger.error('Server start error')
                self._logger.debug(str(e))
                self._stop_event.set()
                return
            s.listen(1)
            s.settimeout(5)
            s.setblocking(False)
            selector = selectors.DefaultSelector()
            selector.register(
                s,
                selectors.EVENT_READ,
                data=ConnectionAcceptor(
                    selector, self._in_queue, self._out_queue, self._logger
                ),
            )

            self._logger.info('Server started')

            sender = ServerSender(selector, self._in_queue, self._logger)
            self._started.set()

            while True:
                try:
                    if self._stop_event.is_set():
                        break
                    events = selector.select(timeout=1)
                    if not events:
                        continue

                    for key, mask in events:
                        if mask & selectors.EVENT_READ:
                            callback = key.data
                            callback(key.fileobj)

                    ready_to_write = [
                        key.fileobj
                        for key, mask in events
                        if mask & selectors.EVENT_WRITE
                    ]
                    if ready_to_write:
                        sender(cast(List[socket.socket], ready_to_write))

                except Exception as e:
                    self._logger.exception(str(e))

            selector.close()
        self._logger.info('Server stopped')
