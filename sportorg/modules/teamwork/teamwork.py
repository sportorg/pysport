import logging
from queue import Empty, Queue
from threading import Event, main_thread
from typing import List, Optional

try:
    from PySide6.QtCore import QThread, Signal
except ModuleNotFoundError:
    from PySide2.QtCore import QThread, Signal

from sportorg.common.singleton import singleton

from .client import ClientThread
from .crypto import TeamworkCipher, TeamworkCryptoError
from .packet_header import Operations
from .server import Command, ServerThread


class ResultThread(QThread):
    data_sender = Signal(object)

    def __init__(self, queue, stop_event, logger=None):
        super().__init__()
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        self._logger.debug("Teamwork result start")
        while True:
            try:
                cmd = self._queue.get(timeout=5)
                self.data_sender.emit(cmd)

            except Empty:
                if not main_thread().is_alive() or self._stop_event.is_set():
                    break
            except Exception as e:
                self._logger.debug(str(e))
        self._logger.debug("Teamwork result shutdown")


@singleton
class Teamwork:
    def __init__(self):
        self._in_queue = Queue()
        self._out_queue = Queue()
        self._stop_event = Event()
        self.factory = {"client": ClientThread, "server": ServerThread}
        self._thread = None
        self._result_thread = None
        self._call_back = None
        self._logger = logging.root

        self.host = ""
        self.port = 50010
        self.connection_type = "client"
        self.encryption_enabled = False
        self.encryption_key = ""

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def set_options(
        self,
        host,
        port,
        connection_type,
        encryption_enabled=False,
        encryption_key="",
    ):
        self.host = host
        self.port = port
        self.connection_type = connection_type
        self.encryption_enabled = encryption_enabled
        self.encryption_key = encryption_key

    def _start_thread(self):
        if self.connection_type not in self.factory.keys():
            return
        cipher = self._get_cipher()
        if self.encryption_enabled and cipher is None:
            self._stop_event.set()
            return
        if self._thread is None:
            self._thread = self.factory[self.connection_type](
                (self.host, self.port),
                self._in_queue,
                self._out_queue,
                self._stop_event,
                self._logger,
                cipher=cipher,
            )
            self._thread.start()
        elif not self._thread.is_alive():
            self._thread = None
            self._start_thread()

    def _start_result_thread(self):
        if self._result_thread is None:
            self._result_thread = ResultThread(
                self._out_queue, self._stop_event, self._logger
            )
            if self._call_back is not None:
                self._result_thread.data_sender.connect(self._call_back)
            self._result_thread.start()
        # elif not self._result_thread.is_alive():
        elif self._result_thread.isFinished():
            self._result_thread = None
            self._start_result_thread()

    def is_alive(self):
        return (
            self._thread is not None
            and self._thread.is_alive()
            and self._result_thread is not None
            and not self._result_thread.isFinished()
        )

    def stop(self):
        self._stop_event.set()

    def start(self):
        self._stop_event.clear()
        self._in_queue.queue.clear()
        self._out_queue.queue.clear()

        self._start_thread()
        if self._thread is None or not self._thread.is_alive():
            return
        self._start_result_thread()

    def toggle(self):
        if self.is_alive():
            self.stop()
            self._logger.info("{} stopping".format(self.connection_type.upper()))
        else:
            self.start()
            self._logger.info("{} starting".format(self.connection_type.upper()))

    def send(self, data, op=Operations.Update.name):
        """data is Dict or List[Dict]"""
        if self.is_alive():
            if isinstance(data, list):
                for item in data:
                    self._in_queue.put(Command(item, op))
                return

            self._in_queue.put(Command(data, op))

    def delete(self, data):
        """data is Dict or List[Dict]"""
        if self.is_alive():
            pass

    def get_server_clients(self) -> List[dict]:
        if not self.is_alive() or self.connection_type != "server":
            return []
        if self._thread is None or not hasattr(self._thread, "get_clients"):
            return []
        return self._thread.get_clients()

    def disconnect_server_client(self, client_id: int) -> None:
        if not self.is_alive() or self.connection_type != "server":
            return
        if self._thread is None or not hasattr(self._thread, "disconnect_client"):
            return
        self._thread.disconnect_client(client_id)

    def _get_cipher(self) -> Optional[TeamworkCipher]:
        if not self.encryption_enabled:
            return None
        try:
            return TeamworkCipher(self.encryption_key)
        except TeamworkCryptoError as e:
            self._logger.error(str(e))
            return None


def configure_teamwork_from_settings(
    connection_type: Optional[str] = None, host: Optional[str] = None
) -> None:
    from sportorg import settings

    current_connection_type = str(
        connection_type or settings.SETTINGS.teamwork_type_connection or "client"
    )

    current_host = str(settings.SETTINGS.teamwork_host or "localhost")
    runtime_host = host if host is not None else current_host
    if current_connection_type == "server" and host is None:
        runtime_host = "0.0.0.0"

    try:
        port = int(settings.SETTINGS.teamwork_port)
    except (TypeError, ValueError):
        port = 50010

    Teamwork().set_options(
        runtime_host,
        port,
        current_connection_type,
        encryption_enabled=bool(settings.SETTINGS.teamwork_encryption_enabled),
        encryption_key=str(settings.SETTINGS.teamwork_encryption_key or ""),
    )
