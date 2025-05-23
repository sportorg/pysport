#!/usr/bin/env python
#
#    Copyright 2023 SRPgroup <SRPgroup@yandex.ru>
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

"""srpid.py - Classes SRPid v1.5"""

import time
from datetime import datetime

from serial import Serial
from serial.serialutil import SerialException
from six import PY3, byte2int, int2byte, iterbytes, print_


# ================================================
#                                         Classs  SRPid
#                                  for master station connect
# ================================================
class SRPid:
    # ------------------------------------------------------------------------------------
    #                                                 INIT
    #                              communication with master station
    #                                  by possible scan COMports
    # ------------------------------------------------------------------------------------
    def __init__(self, port=None, debug=False, logger=None):
        self._serial = None
        self._log_info = print_
        self._log_debug = lambda s: None

        if debug:
            self._log_debug = print_

        if logger is not None:
            if callable(logger.debug):
                self._log_debug = logger.debug
            if callable(logger.info):
                self._log_info = logger.info
        porterrors = ""
        # port from argv
        if port is not None:
            self._conn_m_station(port)
            return
        else:
            scan_ports = ["COM" + str(i + 1) for i in range(64)]
            if len(scan_ports) == 0:
                porterrors = "not found"

            for port in scan_ports:
                try:
                    self._conn_m_station(port)
                    return

                except SRPidException as msg:
                    porterrors += "%s: %s\n" % (port, msg)

        raise SRPidException("Not Station \n%s" % porterrors)

    # ------------------------------------------------------------------------------------
    #                                          TRY CONNECT
    # ------------------------------------------------------------------------------------
    def _conn_m_station(self, port):
        try:
            self._serial = Serial(port, baudrate=9600, timeout=5)
            time.sleep(3)
        except (SerialException, OSError):
            raise SRPidException("Not open ")

        try:
            self._serial.reset_input_buffer()
        except (SerialException, OSError):
            raise SRPidException("Not flush '%s'" % port)

        self.port = port
        self.baudrate = self._serial.baudrate

        msver = self.read_ver()
        if msver is not None:
            self._log_info("port '%s' connect" % port)
            self._log_info("Ver '%s' " % msver)

    # ------------------------------------------------------------------------------------
    #                                        RD  VERSION
    # ------------------------------------------------------------------------------------
    def read_ver(self):
        """master station fw ver"""
        code, data = self._send_command(b"\x32")
        if code == b"\x72":
            return byte2int(data)
        return None

    # ------------------------------------------------------------------------------------
    #                                        SEND COMMAND
    # ------------------------------------------------------------------------------------

    def _send_command(self, code, wait_response=True, timeout=None):
        cs = self._CRCsum(
            code + b"\0" + b"\0" + b"\0" + b"\0" + b"\0" + b"\0" + b"\xce"
        )
        cmd = (
            b"\xc1"
            + code
            + b"\0"
            + b"\0"
            + b"\0"
            + b"\0"
            + b"\0"
            + b"\0"
            + b"\xce"
            + cs
        )

        #        self._log_debug("%s" % ' '.join(hex(byte2int(c)) for c in cmd))
        self._log_debug("request")

        self._serial.flushInput()
        self._serial.write(cmd)

        if wait_response:
            resp_code, data = self._get_response(timeout)
            return SRPid._preprocess_response(resp_code, data, self._log_debug)

        return None

    # ------------------------------------------------------------------------------------
    #                                                SEARCH CHIP
    # ------------------------------------------------------------------------------------
    def search_chip(self):
        """search_chip   self.chip_data  return status"""

        try:
            self.chip_data = self.read_chip(timeout=0.5)
            return True

        except SRPidTimeout:
            pass

        except SRPidException as msg:
            self._log_debug("Warning: %s" % msg)
        return False

    # ------------------------------------------------------------------------------------
    #                                             READ CHIP
    # ------------------------------------------------------------------------------------
    def read_chip(self, timeout=None):
        """Timeout  pyserial doc
        return    dict  chip_data
        """
        code, data = self._send_command(b"\x2f", timeout=timeout)
        if code == b"\x70":
            return self._parse_chip_data(data)
        else:
            raise SRPidException("Read chip failed.")

    # ------------------------------------------------------------------------------------
    #                                         GET RESPONSE
    # ------------------------------------------------------------------------------------
    def _get_response(self, timeout=None, wait_part=None):
        try:
            if timeout is not None:
                old_timeout = self._serial.timeout
                self._serial.timeout = timeout

            # Find START_BYTE

            while True:
                byte = self._serial.read()
                if byte == b"":
                    raise SRPidTimeout("No connect")
                elif byte == b"\xec":  # START_BYTE_A
                    break

            if timeout is not None:
                self._serial.timeout = old_timeout

            code = self._serial.read()
            length_byte = self._serial.read()
            length = byte2int(length_byte)
            data = self._serial.read(length)
            chk_sum = self._serial.read()

            self._log_debug("answer")

            if not SRPid._cs_check(code + length_byte + data, chk_sum):
                raise SRPidException("Checksum mismatch")

        except (SerialException, OSError) as msg:
            raise SRPidException("Error get response: %s" % msg)

        return code, data

    # ------------------------------------------------------------------------------------
    #                                             BEEP   OK
    # ------------------------------------------------------------------------------------
    def beep_ok(self):
        self._send_command(b"\x36", wait_response=False)

    # ------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------
    def disconnect(self):
        """Close the serial port an disconnect from the station."""
        self._serial.close()

    # ------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------
    def reconnect(self):
        """Close the serial port and reopen again."""
        self.disconnect()
        self._conn_m_station(self._serial.port)

    # ------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------
    def __del__(self):
        if self._serial is not None:
            self._serial.close()

    # ------------------------------------------------------------------------------------
    #                                           staticmethods
    # ------------------------------------------------------------------------------------
    @staticmethod
    def _to_int(s):
        """Compute the integer value of a raw byte string (big endianes)."""
        value = 0
        for offset, c in enumerate(iterbytes(s[::-1])):
            value += c << offset * 8
        return value

    # ------------------------------------------------------------------------------------
    #                                           staticmethods
    # ------------------------------------------------------------------------------------
    @staticmethod
    def _to_str(i, len):
        """
        @param i:   Integer to convert into str
        @param len: Length of the return value. If i does not fit OverflowError is raised.
        @return:    string representation of i (MSB first)
        """
        if PY3:
            return i.to_bytes(len, "big")
        if i >> len * 8 != 0:
            raise OverflowError("%i too big to convert to %i bytes" % (i, len))
        string = b""
        for offset in range(len - 1, -1, -1):
            string += int2byte((i >> offset * 8) & 0xFF)
        return string

    # ------------------------------------------------------------------------------------
    #                                           staticmethods
    # ------------------------------------------------------------------------------------
    @staticmethod
    def _preprocess_response(code, data, log_debug):
        if code == b"\x76":  # _ERROR
            if data == b"\x01":
                raise SRPidException("ComError")
            elif data == b"\x02":
                raise SRPidException("WrError")
            elif data == b"\x03":
                raise SRPidException("RdError")
            else:
                raise SRPidException("Error with code %s" % hex(byte2int(code)))
        elif code == b"\x75":  # _OK
            log_debug("Ok")
        return code, data

    # ------------------------------------------------------------------------------------
    #                                           staticmethods
    # ------------------------------------------------------------------------------------
    @staticmethod
    def _CRCsum(s):
        """Compute chk_sum of value.
        @param s: byte string
        """
        sum = 0
        for c in s:
            sum += c
        sum &= 0xFF
        return int2byte(sum)

    # ------------------------------------------------------------------------------------
    #                                           staticmethods
    # ------------------------------------------------------------------------------------
    @staticmethod
    def _cs_check(s, chk_sum):
        return SRPid._CRCsum(s) == chk_sum

    # ------------------------------------------------------------------------------------
    #                                           staticmethods
    # ------------------------------------------------------------------------------------
    @staticmethod
    def _parse_chip_data(data):
        # TODO check data length
        result = {}
        #        result['SerialNum'] = SRPid._to_int(data[0:4])
        result["ChipNum"] = SRPid._to_int(data[4:6])
        #        result['Reserv'] = data[6:14]
        result["CP"] = []
        for i in range(14, len(data), 5):
            cp = data[i]
            time = datetime.fromtimestamp(SRPid._to_int(data[i + 1 : i + 5]))
            result["CP"].append((cp, time))
        return result


# ================================================
#                                             Classs
# ================================================
class SRPidException(Exception):
    pass


# ================================================
#                                             Classs
# ================================================
class SRPidTimeout(SRPidException):
    pass
