import queue
import socket
from threading import Thread, main_thread
import json

from .server import Command
from .packet_header import Header, Operations


class ClientSenderThread(Thread):
    def __init__(self, conn, in_queue, stop_event, logger=None):
        super().__init__()
        self.setName(self.__class__.__name__)
        self.conn = conn
        self._in_queue = in_queue
        self._stop_event = stop_event
        self._logger = logger

    def run(self):
        self._logger.debug('Client sender start')
        while True:
            try:
                cmd = self._in_queue.get(timeout=5)
                self.conn.sendall(cmd.get_packet())
            except queue.Empty:
                if not main_thread().is_alive() or self._stop_event.is_set():
                    break
            except ConnectionResetError as e:
                self._logger.debug(str(e))
                break
            except Exception as e:
                self._logger.debug(str(e))
                break
        self.conn.close()
        self._logger.debug('Client sender shutdown')
        self._stop_event.set()


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
        self.conn.settimeout(5)
        self._logger.debug('Client receiver start')
        hdr = Header()
        is_new_pack = True

        while True:
            try:
                data = self.conn.recv(1024)
                if not data:
                    break
                full_data += data
                # self._logger.debug('Client got data: {}'.format(full_data))
                while True:
                    # getting Header
                    if is_new_pack:
                        if len(full_data) >= hdr.header_size:
                            hdr.unpack_header(full_data[:hdr.header_size])
                            # self._logger.debug('Client Packet Header: {}, ver: {}, size: {}'.format(full_data[:hdr.header_size], hdr.version, hdr.size))
                            full_data = full_data[hdr.header_size:]
                            is_new_pack = False
                        else:
                            break
                    # Getting JSON data
                    else:
                        if len(full_data) >= hdr.size:
                            command = Command(json.loads(full_data[:hdr.size].decode()), Operations(hdr.opType).name)
                            self._out_queue.put(command)  # for local
                            full_data = full_data[hdr.size:]
                            is_new_pack = True
                        else:
                            break
            except socket.timeout:
                if not main_thread().is_alive() or self._stop_event.is_set():
                    break
            except ConnectionAbortedError as e:
                self._logger.exception(e)
                break
            except ConnectionResetError as e:
                self._logger.exception(e)
                break
            except Exception as e:
                self._logger.exception(e)
                break
        self._logger.debug('Client receiver shutdown')
        self._stop_event.set()


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
                self._logger.info('Client start')
                sender = ClientSenderThread(s, self._in_queue, self._stop_event, self._logger)
                sender.start()
                receiver = ClientReceiverThread(s, self._out_queue, self._stop_event, self._logger)
                receiver.start()

                sender.join()
                receiver.join()

            except ConnectionRefusedError as e:
                self._logger.exception(e)
                return
            except Exception as e:
                self._logger.exception(e)
                return

        s.close()
        self._logger.info('Client shutdown')
