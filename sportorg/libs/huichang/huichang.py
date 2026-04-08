#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2025,2026 Semyon Yakimov <sdyakimov@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


from datetime import datetime, time
from serial import Serial
from serial.serialutil import SerialException

from sportorg.language import translate


class Huichang(object):
    START_SEQUENCE = b"\xaa\xbb\xff"

    CMD_TIME_SYNC = b"\x0a"
    CMD_CARD_DATA = b"\x20"
    CMD_SET_MASTER_MODE = b"\x28"
    CMD_SET_CP_NUMBER = b"\x29"
    CMD_CONTACT_CARD_DATA = b"\x60"
    CMD_WRITE_FINGER_NAME = b"\x64"
    CMD_READ_FINGER_NAME = b"\x65"
    CMD_CARD_BATTERY_LEVEL = b"\xa1"

    def __init__(self, port=None, debug=False, logger=None):
        self._serial = None
        self._log_info = print
        self._log_debug = lambda s: None
        self._connected = False

        if debug:
            self._log_debug = print
        if logger:
            if callable(logger.debug):
                self._log_debug = logger.debug
            if callable(logger.info):
                self._log_info = logger.info

        if not port:
            raise HuichangException(translate("No port specified"))
        self._connect_master_station(port)
        self.switch_to_online_mode()

    def __del__(self):
        self.disconnect()

    @property
    def connected(self):
        return self._connected

    def disconnect(self):
        if self._serial is not None:
            if self._serial.is_open and self._connected:
                self.switch_to_offline_mode()
            self._connected = False
            self._log_info(translate("Disconnect from Huichang station"))
            self._serial.close()

    def send_command(self, cmd, params=None, wait_response=True, timeout=None):
        if params is None:
            params = b""
        if self._serial is None:
            raise HuichangException(translate("Not connected to Huichang station"))

        datalen = len(params) + 1
        crc = self.crc8(params)
        packet = self.START_SEQUENCE + cmd + bytes([datalen]) + params + bytes([crc])

        self._log_debug("=> 0x {}".format(" ".join(f"{b:02x}" for b in packet)))

        self._serial.flushInput()
        self._serial.write(packet)

        if wait_response:
            return self.read_and_parse_response(timeout)

        return None

    def switch_to_online_mode(self):
        self._set_master_mode(online=True)

    def switch_to_offline_mode(self):
        self._set_master_mode(online=False)

    def _set_master_mode(self, online):
        time = datetime.now()
        params = b""
        params += bytes([time.hour])
        params += bytes([time.minute])
        params += bytes([time.second])
        if online:
            params += b"\x02"
        else:
            params += b"\x01"
        self.send_command(self.CMD_SET_MASTER_MODE, params)

    def time_sync(self):
        time = datetime.now()
        params = b""
        params += bytes([time.hour])
        params += bytes([time.minute])
        params += bytes([time.second])
        self.send_command(self.CMD_TIME_SYNC, params)

    def set_station_number(self, cp_number):
        time = datetime.now()
        params = b""
        params += bytes([time.hour])
        params += bytes([time.minute])
        params += bytes([time.second])
        params += bytes([cp_number])
        self.send_command(self.CMD_SET_CP_NUMBER, params)

    def _connect_master_station(self, port):
        try:
            self._log_info(translate("Open port {}").format(port))
            self._serial = Serial(port, baudrate=9600, timeout=3)
        except (SerialException, OSError):
            raise HuichangException(translate("Could not open port {}").format(port))

    def read_and_parse_response(self, timeout):
        resp_code, data = self._read_response(timeout)
        return self._process_response(resp_code, data)

    def wait_card_data(self):
        try:
            return self.read_and_parse_response(timeout=0.5)
        except HuichangTimeout:
            pass
        return None

    def _read_response(self, timeout=None):
        if self._serial is None:
            raise HuichangException(translate("Not connected to master station"))
        serial = self._serial

        if timeout is not None:
            old_timeout = serial.timeout
            serial.timeout = timeout

        try:
            # Skip any bytes before start sequence
            while True:
                byte = serial.read()
                if byte == b"":
                    raise HuichangTimeout(
                        translate("No response from Huichang station")
                    )
                elif (
                    byte == bytes([Huichang.START_SEQUENCE[0]])
                    and serial.read() == bytes([Huichang.START_SEQUENCE[1]])
                    and serial.read() == bytes([Huichang.START_SEQUENCE[2]])
                ):
                    break
                elif (
                    byte == b"\x1b"
                    and serial.read() == b"\x40"
                    and serial.read() == b"\x20"
                    and serial.read() == b"\x0d"
                    and serial.read() == b"\x0a"
                ):
                    # Station send internal punching data to print
                    self._log_info(translate("Internal station data:"))
                    s = ""
                    while True:
                        byte = serial.read()
                        if byte == b"" or byte == b"\x1b":
                            break
                        s += byte.decode()
                    self._log_info(s)
                    return None, None
                self._log_debug(
                    "Skipping byte: 0x {}".format(" ".join(f"{b:02x}" for b in byte))
                )

            cmd_code = serial.read()
            length_byte = serial.read()
            length = length_byte[0]
            if length < 1:
                raise HuichangException(f"Invalid length: {length}")

            read_more_fragments = False
            if (
                cmd_code in [Huichang.CMD_CARD_DATA, Huichang.CMD_CONTACT_CARD_DATA]
                and length > 1
            ):
                read_more_fragments = True

            payload = serial.read(length - 1)
            crc = serial.read()
            self._log_debug(
                "<= code 0x{:02x}, length {}, crc 0x{:02x} payload: 0x {}".format(
                    cmd_code[0], length, crc[0], " ".join(f"{b:02x}" for b in payload)
                )
            )
            # Ignore CRC for CMD_CARD_BATTERY_LEVEL
            if cmd_code != Huichang.CMD_CARD_BATTERY_LEVEL:
                crc_calc = self.crc8(payload)
                if not crc_calc == crc[0]:
                    # self._log_debug("CRC mismatch: 0x{:02x} != 0x{:02x}".format(crc_calc, crc[0]))
                    raise HuichangException("CRC mismatch")

        except (SerialException, OSError) as msg:
            raise HuichangException(f"Error reading response: {msg}")
        finally:
            if timeout is not None:
                serial.timeout = old_timeout

        if read_more_fragments:
            next_cmd_code, next_data = self._read_response(timeout)
            if next_cmd_code == cmd_code:
                payload += next_data
            else:  # got an error
                return next_cmd_code, next_data

        return cmd_code, payload

    def _process_response(self, cmd_code, data):
        if (
            cmd_code in [Huichang.CMD_SET_MASTER_MODE, Huichang.CMD_TIME_SYNC]
            and len(data) == 1
        ):
            if data == b"\xcc":
                self._log_debug("Success")
                self._connected = True
            elif data == b"\xee":
                raise HuichangException("Device returned error")
        elif cmd_code in [Huichang.CMD_CARD_DATA, Huichang.CMD_CONTACT_CARD_DATA]:
            ret = {}
            ret["card_number"] = int(data[0:4].hex())
            ret["start"] = self._to_time(data[5:9])
            ret["finish"] = self._to_time(data[10:14])
            ret["clear"] = self._to_time(data[15:18])
            ret["punches"] = []
            for i in range(18, len(data), 4):
                cp_code = data[i]
                cp_time = self._to_time(data[i + 1 : i + 4])
                ret["punches"].append((cp_code, cp_time))

            if cmd_code == Huichang.CMD_CARD_DATA:
                # Wait packet with battery level
                try:
                    next_cmd_code, next_data = self._read_response(timeout=0.2)
                    if next_cmd_code == Huichang.CMD_CARD_BATTERY_LEVEL:
                        ret["battery_level"] = int(next_data[0])
                    else:
                        # another packet received
                        ret["battery_level"] = None
                except HuichangTimeout:
                    ret["battery_level"] = None

            self._log_debug(f"Card data: {ret}")
            return ret
        elif cmd_code == Huichang.CMD_CARD_BATTERY_LEVEL:
            self._log_debug(f"Card battery: {data[0]}%")

        return None

    @staticmethod
    def _to_time(data: bytes) -> time:
        if data[0] > 23 or data[1] > 59 or data[2] > 59:
            return time()
        ms = 0
        if len(data) > 3:
            ms = data[3]
        return time(hour=data[0], minute=data[1], second=data[2], microsecond=ms * 1000)

    @staticmethod
    def crc8(data: bytes) -> int:
        poly = 29
        crc = 0xFF  # init

        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ poly) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        crc ^= 0x00  # xorout
        return crc


class HuichangException(Exception):
    pass


class HuichangTimeout(HuichangException):
    pass


if __name__ == "__main__":
    hc = Huichang("/dev/ttyACM0", debug=True)
    while True:
        try:
            hc.wait_card_data()
        except HuichangException as msg:
            print(f"Warning: {msg}")
