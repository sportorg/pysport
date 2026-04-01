import queue
import selectors
import socket
import time
from threading import Event, Thread
from typing import Optional, Tuple, cast

import orjson

from .command import Command
from .crypto import TeamworkCipher, TeamworkCryptoError
from .packet_header import Header, Operations


class ClientSender:
    def __init__(self, in_queue: queue.Queue, cipher: Optional[TeamworkCipher] = None):
        self._in_queue = in_queue
        self._cipher = cipher

    def __call__(self, conn: socket.socket) -> bool:
        sent = False
        try:
            while True:
                cmd = self._in_queue.get(timeout=0.1)
                conn.sendall(cmd.get_packet(self._cipher))
                sent = True
        except queue.Empty:
            return sent


class ClientReceiver:
    MSG_SIZE = 1024

    def __init__(self, out_queue: queue.Queue, cipher: Optional[TeamworkCipher] = None):
        self._out_queue = out_queue
        self._cipher = cipher
        self._full_data = b""
        self._hdr = Header()
        self._is_new_pack = True

    def __call__(self, conn: socket.socket) -> bool:
        try:
            data = conn.recv(self.MSG_SIZE)
        except OSError:
            return False
        if not data:
            return False
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
                    packet = self._full_data[: self._hdr.size]
                    payload = self._decode_payload(packet)
                    command = Command(
                        orjson.loads(payload), Operations(self._hdr.op_type).name
                    )
                    self._out_queue.put_nowait(command)
                    self._full_data = self._full_data[self._hdr.size :]
                    self._is_new_pack = True
                else:
                    break
        return True

    def _decode_payload(self, packet: bytes) -> bytes:
        if self._cipher is None:
            if self._hdr.version != Header.VERSION_PLAIN:
                raise TeamworkCryptoError(
                    "Encrypted teamwork packet received, but encryption is disabled"
                )
            return packet

        if self._hdr.version != Header.VERSION_AES256_GCM:
            raise TeamworkCryptoError(
                "Unencrypted teamwork packet received, but encryption is enabled"
            )
        return self._cipher.decrypt(packet)


class ClientThread(Thread):
    def __init__(
        self,
        addr: Tuple[str, int],
        in_queue: queue.Queue,
        out_queue: queue.Queue,
        stop_event: Event,
        logger,
        keepalive_interval: float = 5.0,
        cipher: Optional[TeamworkCipher] = None,
    ):
        super().__init__()
        self.setName("Teamwork Client")
        self._addr = addr
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._stop_event = stop_event
        self._logger = logger
        self._started = Event()
        self._keepalive_interval = keepalive_interval
        self._cipher = cipher

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
                self._logger.info("Client started")
                self._started.set()
                sender = ClientSender(self._in_queue, self._cipher)
                receiver = ClientReceiver(self._out_queue, self._cipher)
                last_outgoing_packet_time = time.monotonic()

                while True:
                    if self._stop_event.is_set():
                        break
                    disconnected = False
                    events = selector.select(timeout=1)
                    for key, mask in events:
                        if mask & selectors.EVENT_READ:
                            try:
                                if not receiver(cast(socket.socket, key.fileobj)):
                                    disconnected = True
                                    break
                            except TeamworkCryptoError as e:
                                self._logger.error(str(e))
                                disconnected = True
                                break
                        if mask & selectors.EVENT_WRITE:
                            try:
                                if sender(cast(socket.socket, key.fileobj)):
                                    last_outgoing_packet_time = time.monotonic()
                            except OSError:
                                disconnected = True
                                break

                    if disconnected:
                        self._logger.info("Teamwork server disconnected")
                        self._stop_event.set()
                        break

                    if (
                        time.monotonic() - last_outgoing_packet_time
                        >= self._keepalive_interval
                    ):
                        try:
                            s.sendall(
                                Command(None, Operations.Read.name).get_packet(
                                    self._cipher
                                )
                            )
                        except OSError:
                            self._logger.info("Teamwork server disconnected")
                            self._stop_event.set()
                            break
                        last_outgoing_packet_time = time.monotonic()
            except OSError as e:
                self._logger.error(str(e))
                self._stop_event.set()
            except Exception as e:
                self._logger.exception(e)
                self._stop_event.set()
            finally:
                selector.close()
        self._logger.info("Client stopped")
