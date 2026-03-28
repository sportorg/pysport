import selectors
import socket
import time
from queue import Empty, Queue
from threading import Event, Lock, Thread
from typing import Dict, List, Tuple, cast

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
        server_thread,
        logger,
    ):
        self._selector = selector
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._server_thread = server_thread
        self._logger = logger
        self._full_data = b""
        self._hdr = Header()
        self._is_new_pack = True

    def __call__(self, sock: socket.socket) -> None:
        try:
            data = sock.recv(self.MSG_SIZE)
            if not data:
                self._server_thread.disconnect_socket(sock, self._selector)
                return
        except OSError as e:
            self._logger.error(str(e))
            self._server_thread.disconnect_socket(sock, self._selector)
            return

        self._full_data += data
        while True:
            if self._is_new_pack:
                if len(self._full_data) >= self._hdr.header_size:
                    self._hdr.unpack_header(self._full_data[: self._hdr.header_size])
                    self._full_data = self._full_data[self._hdr.header_size :]
                    self._is_new_pack = False
                else:
                    break
            else:
                if len(self._full_data) >= self._hdr.size:
                    packet = self._full_data[: self._hdr.size]
                    self._full_data = self._full_data[self._hdr.size :]
                    self._is_new_pack = True
                    self._process_packet(packet, sock)
                else:
                    break

    def _process_packet(self, packet: bytes, sock: socket.socket) -> None:
        try:
            operation = Operations(self._hdr.op_type).name
        except ValueError:
            self._logger.error("Unsupported teamwork operation: %s", self._hdr.op_type)
            return

        try:
            command = Command(orjson.loads(packet), operation, sender=sock)
        except Exception as e:
            self._logger.error(str(e))
            return

        if command.is_service_keepalive():
            self._server_thread.mark_keepalive(sock)
            return

        self._server_thread.mark_data_packet(sock)
        self._out_queue.put(command)
        self._in_queue.put(command)


class ServerSender:
    def __init__(
        self,
        selector: selectors.BaseSelector,
        in_queue: Queue,
        server_thread,
        logger,
    ):
        self._selector = selector
        self._in_queue = in_queue
        self._server_thread = server_thread
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
                        self._server_thread.disconnect_socket(sock, self._selector)
        except Empty:
            pass


class ConnectionAcceptor:
    def __init__(
        self,
        selector: selectors.BaseSelector,
        in_queue: Queue,
        out_queue: Queue,
        server_thread,
        logger,
    ):
        self._selector = selector
        self._logger = logger
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._server_thread = server_thread

    def __call__(self, sock: socket.socket) -> None:
        conn, addr = sock.accept()
        conn.setblocking(False)
        client_id = self._server_thread.add_client(conn, addr)
        self._selector.register(
            conn,
            selectors.EVENT_READ | selectors.EVENT_WRITE,
            data=ServerReceiver(
                self._selector,
                self._in_queue,
                self._out_queue,
                self._server_thread,
                self._logger,
            ),
        )
        self._logger.info(
            "Teamwork client connected: id=%s addr=%s:%s",
            client_id,
            addr[0],
            addr[1],
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
        self.setName("Teamwork Server")
        self.addr = addr
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._stop_event = stop_event
        self._logger = logger
        self._started = Event()
        self._disconnect_queue: Queue = Queue()
        self._clients_lock = Lock()
        self._clients: Dict[socket.socket, Dict[str, object]] = {}
        self._clients_by_id: Dict[int, socket.socket] = {}
        self._next_client_id = 1

    def wait(self) -> None:
        self._started.wait()

    def add_client(self, sock: socket.socket, addr: Tuple[str, int]) -> int:
        now = time.time()
        with self._clients_lock:
            client_id = self._next_client_id
            self._next_client_id += 1
            self._clients[sock] = {
                "id": client_id,
                "host": addr[0],
                "port": addr[1],
                "connected_at": now,
                "last_seen_at": now,
                "packets": 0,
                "keepalive_packets": 0,
            }
            self._clients_by_id[client_id] = sock
        return client_id

    def get_clients(self) -> List[Dict[str, object]]:
        now = time.time()
        with self._clients_lock:
            clients = [
                {
                    "id": item["id"],
                    "host": item["host"],
                    "port": item["port"],
                    "address": "{}:{}".format(item["host"], item["port"]),
                    "connected_at": item["connected_at"],
                    "last_seen_at": item["last_seen_at"],
                    "idle_seconds": round(
                        max(0.0, now - cast(float, item["last_seen_at"])), 1
                    ),
                    "packets": item["packets"],
                    "keepalive_packets": item["keepalive_packets"],
                }
                for item in self._clients.values()
            ]
        clients.sort(key=lambda item: cast(int, item["id"]))
        return clients

    def disconnect_client(self, client_id: int) -> None:
        self._disconnect_queue.put(client_id)

    def disconnect_socket(
        self, sock: socket.socket, selector: selectors.BaseSelector
    ) -> None:
        self._disconnect_socket(sock, selector)

    def mark_keepalive(self, sock: socket.socket) -> None:
        self._mark_client_activity(sock, keepalive=True)

    def mark_data_packet(self, sock: socket.socket) -> None:
        self._mark_client_activity(sock, keepalive=False)

    def _mark_client_activity(self, sock: socket.socket, keepalive: bool) -> None:
        now = time.time()
        with self._clients_lock:
            item = self._clients.get(sock)
            if item is None:
                return
            item["last_seen_at"] = now
            if keepalive:
                item["keepalive_packets"] = cast(int, item["keepalive_packets"]) + 1
            else:
                item["packets"] = cast(int, item["packets"]) + 1

    def _disconnect_socket(
        self, sock: socket.socket, selector: selectors.BaseSelector
    ) -> None:
        with self._clients_lock:
            client = self._clients.pop(sock, None)
            if client is not None:
                self._clients_by_id.pop(cast(int, client["id"]), None)

        try:
            selector.unregister(sock)
        except Exception:
            pass

        try:
            sock.close()
        except OSError:
            pass

        if client is not None:
            self._logger.info(
                "Teamwork client disconnected: id=%s addr=%s:%s",
                client["id"],
                client["host"],
                client["port"],
            )

    def _apply_disconnect_requests(self, selector: selectors.BaseSelector) -> None:
        while True:
            try:
                client_id = self._disconnect_queue.get_nowait()
            except Empty:
                return

            with self._clients_lock:
                sock = self._clients_by_id.get(client_id)
            if sock is not None:
                self._disconnect_socket(sock, selector)

    def run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                s.bind(self.addr)
            except Exception as e:
                self._logger.error("Server start error")
                self._logger.debug(str(e))
                self._stop_event.set()
                return
            s.listen(10)
            s.settimeout(5)
            s.setblocking(False)
            selector = selectors.DefaultSelector()
            selector.register(
                s,
                selectors.EVENT_READ,
                data=ConnectionAcceptor(
                    selector,
                    self._in_queue,
                    self._out_queue,
                    self,
                    self._logger,
                ),
            )

            self._logger.info("Server started")

            sender = ServerSender(selector, self._in_queue, self, self._logger)
            self._started.set()

            while True:
                try:
                    if self._stop_event.is_set():
                        break

                    self._apply_disconnect_requests(selector)
                    events = selector.select(timeout=1)

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

            with self._clients_lock:
                sockets = list(self._clients.keys())
            for sock in sockets:
                self._disconnect_socket(sock, selector)

            selector.close()
        self._logger.info("Server stopped")
