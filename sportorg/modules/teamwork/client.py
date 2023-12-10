import queue
import selectors
import socket
from threading import Event, Thread
from typing import Tuple, cast

import orjson

from .command import Command
from .packet_header import Header, Operations


class ClientSender:
    def __init__(self, in_queue: queue.Queue):
        self._in_queue = in_queue

    def __call__(self, conn: socket.socket) -> None:
        try:
            while True:
                cmd = self._in_queue.get_nowait()
                conn.sendall(cmd.get_packet())
        except queue.Empty:
            return


class ClientReceiver:
    MSG_SIZE = 1024

    def __init__(self, out_queue: queue.Queue):
        self._out_queue = out_queue
        self._full_data = b''
        self._hdr = Header()
        self._is_new_pack = True

    def __call__(self, conn: socket.socket) -> None:
        data = conn.recv(self.MSG_SIZE)
        if not data:
            return
        self._full_data += data
        while True:
            # getting Header
            if self._is_new_pack:
                if len(self._full_data) >= self._hdr.header_size:
                    self._hdr.unpack_header(self._full_data[: self._hdr.header_size])
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
                    )
                    self._out_queue.put_nowait(command)
                    self._full_data = self._full_data[self._hdr.size :]
                    self._is_new_pack = True
                else:
                    break


class ClientThread(Thread):
    def __init__(
        self,
        addr: Tuple[str, int],
        in_queue: queue.Queue,
        out_queue: queue.Queue,
        stop_event: Event,
        logger,
    ):
        super().__init__()
        self.setName('Teamwork Client')
        self._addr = addr
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._stop_event = stop_event
        self._logger = logger
        self._started = Event()

    def wait(self) -> None:
        self._started.wait()

    def run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            selector = selectors.DefaultSelector()
            try:
                s.connect(self._addr)
                s.settimeout(5)
                s.setblocking(False)
                selector.register(s, selectors.EVENT_READ | selectors.EVENT_WRITE)
                self._logger.info('Client started')
                self._started.set()
                sender = ClientSender(self._in_queue)
                receiver = ClientReceiver(self._out_queue)
                while True:
                    if self._stop_event.is_set():
                        break
                    events = selector.select(timeout=1)
                    if not events:
                        continue
                    for key, mask in events:
                        if mask & selectors.EVENT_READ:
                            receiver(cast(socket.socket, key.fileobj))
                        if mask & selectors.EVENT_WRITE:
                            sender(cast(socket.socket, key.fileobj))
            except Exception as e:
                self._logger.exception(e)
                self._stop_event.set()
            finally:
                selector.close()
        self._logger.info('Client stopped')
