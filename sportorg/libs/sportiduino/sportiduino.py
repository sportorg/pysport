#!/usr/bin/env python
#
#    Copyright 2018 Semyon Yakimov <ya-kimov@mail.ru>
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
"""
sportiduino.py - Classes to work with Sportiduino v1.2.0 and above.
"""

# from binascii import hexlify
import os
import platform
import re
import time
from datetime import datetime

from serial import Serial
from serial.serialutil import SerialException
from six import PY3, byte2int, int2byte, iterbytes, print_

if PY3:

    def byte2int(x):
        try:
            return x[0]
        except TypeError:
            return x


class Sportiduino(object):
    """Protocol functions and constants to interact with Sportiduino master station."""

    # Constants
    START_BYTE = b'\xfe'

    OFFSET = 0x1E

    MAX_DATA_LEN = 28

    START_STATION = 240
    FINISH_STATION = 245

    # Protocol commands
    CMD_INIT_TIMECARD = b'\x41'
    CMD_INIT_CP_NUM_CARD = b'\x42'
    CMD_INIT_PASSWDCARD = b'\x43'
    CMD_INIT_CARD = b'\x44'
    CMD_WRITE_PAGES6_7 = b'\x45'
    CMD_READ_VERS = b'\x46'
    CMD_INIT_BACKUPREADER = b'\x47'
    CMD_READ_BACKUPREADER = b'\x48'
    CMD_SET_READ_MODE = b'\x49'
    CMD_READ_CARD = b'\x4b'
    CMD_READ_RAW = b'\x4c'
    CMD_INIT_SLEEPCARD = b'\x4e'
    CMD_BEEP_ERROR = b'\x58'
    CMD_BEEP_OK = b'\x59'

    # Protocol responses
    RESP_BACKUP = b'\x61'
    RESP_CARD_DATA = b'\x63'
    RESP_CARD_RAW = b'\x65'
    RESP_VERS = b'\x66'
    RESP_MODE = b'\x69'
    RESP_ERROR = b'\x78'
    RESP_OK = b'\x79'

    # Protocol error codes
    ERR_COM = b'\x01'
    ERR_WRITE_CARD = b'\x02'
    ERR_READ_CARD = b'\x03'
    ERR_READ_EEPROM = b'\x04'

    class Version(object):
        """Sportiduino firmware version."""

        def __init__(self, value):
            """Initializes version by byte from master station.
            @param value: Byte from master station.
            """
            self.value = value
            self.major = value // 100
            self.minor = value % 100

        def __str__(self):
            """Override __str__ method.
            @return: User friendly version string.
            """
            return 'v%d.%d.x' % (self.major, self.minor)

    def __init__(self, port=None, debug=False, logger=None):
        """Initializes communication with master station at port.
        @param port: Serial device for the connection. If port is None it
                     scans all available ports and connects to the first
                     reader found.
        """
        self._serial = None

        self._log_info = print_
        self._log_debug = lambda s: None
        if debug:
            self._log_debug = print_

        if logger:
            if callable(logger.debug):
                self._log_debug = logger.debug
            if callable(logger.info):
                self._log_info = logger.info

        errors = ''
        if port:
            self._connect_master_station(port)
            return
        else:
            if platform.system() == 'Linux':
                scan_ports = [
                    os.path.join('/dev', f)
                    for f in os.listdir('/dev')
                    if re.match('ttyUSB.*', f)
                ]
            elif platform.system() == 'Windows':
                scan_ports = ['COM' + str(i) for i in range(32)]
            else:
                raise SportiduinoException(
                    'Unsupported platform: %s' % platform.system()
                )

            if len(scan_ports) == 0:
                errors = 'no serial ports found'

            for port in scan_ports:
                try:
                    self._connect_master_station(port)
                    return
                except SportiduinoException as msg:
                    errors += 'port %s: %s\n' % (port, msg)

        raise SportiduinoException(
            'No Sportiduino master station found. Possible reasons: %s' % errors
        )

    def beep_ok(self):
        """One long beep and blink master station."""
        self._send_command(Sportiduino.CMD_BEEP_OK, wait_response=False)

    def beep_error(self):
        """Three short beep and blink master station."""
        self._send_command(Sportiduino.CMD_BEEP_ERROR, wait_response=False)

    def disconnect(self):
        """Close the serial port an disconnect from the station."""
        self._serial.close()

    def reconnect(self):
        """Close the serial port and reopen again."""
        self.disconnect()
        self._connect_master_station(self._serial.port)

    def read_version(self):
        """Read master station firmware version.
        @return: Version object.
        """
        code, data = self._send_command(Sportiduino.CMD_READ_VERS)
        if code == Sportiduino.RESP_VERS:
            return Sportiduino.Version(byte2int(data))
        return None

    def read_card(self, timeout=None):
        """Reads out the card currently inserted into the station.
        @param timeout: Timeout for reading response (see pyserial doc).
        @return:        Card data in dictionary.
        """
        code, data = self._send_command(Sportiduino.CMD_READ_CARD, timeout=timeout)
        if code == Sportiduino.RESP_CARD_DATA:
            return self._parse_card_data(data)
        else:
            raise SportiduinoException('Read card failed.')

    def poll_card(self):
        """Poll card inserted into the station.
        If card readed update self.card_data and return True.
        @return: Read card status."""
        try:
            self.card_data = self.read_card(timeout=0.5)
            return True
        except SportiduinoTimeout:
            pass
        except SportiduinoException as msg:
            self._log_debug('Warning: %s' % msg)
        return False

    def read_card_raw(self):
        """Reads out the RAW data from card currently inserted into the station.
        @return: RAW card data in dictionary.
        """
        code, data = self._send_command(Sportiduino.CMD_READ_RAW)
        if code == Sportiduino.RESP_CARD_RAW:
            return self._parse_card_raw_data(data)
        else:
            raise SportiduinoException('Read raw data failed.')

    def read_backup(self):
        """Read backup from backupreader card.
        @return: Backup data in dictionary.
        """
        code, data = self._send_command(Sportiduino.CMD_READ_BACKUPREADER)
        if code == Sportiduino.RESP_BACKUP:
            return self._parse_backup(data)
        else:
            raise SportiduinoException('Read backup failed.')

    def init_card(self, card_number, page6=None, page7=None):
        """Initialize card. Set card number, init time and additional pages.
        @param card_number: Card number (eg participant bib).
        @param page6:       Additional page.
        @param page7:       Additional page.
        """
        # TODO: check page6 and page7 length
        if page6 is None:
            page6 = b'\x00\x00\x00\x00'
        if page7 is None:
            page7 = b'\x00\x00\x00\x00'

        params = b''
        params += Sportiduino._to_str(card_number, 2)
        t = int(time.time())
        params += Sportiduino._to_str(t, 4)
        params += page6[:5]
        params += page7[:5]
        self._send_command(Sportiduino.CMD_INIT_CARD, params, wait_response=False)

    def init_backupreader(self):
        """Initialize backupreader card."""
        self._send_command(Sportiduino.CMD_INIT_BACKUPREADER, wait_response=False)

    def init_sleepcard(self):
        """Initialize sleep card."""
        self._send_command(Sportiduino.CMD_INIT_SLEEPCARD, wait_response=False)

    def init_cp_number_card(self, cp_number):
        """Initialize card for writing check point number to base station.
        @param cp_number: Check point number.
        """
        params = int2byte(cp_number)
        self._send_command(Sportiduino.CMD_WRITE_CP_NUM, params, wait_response=False)

    def init_time_card(self, time=datetime.today()):
        """Initialize card for writing time to base station.
        @param time: Time for base station (default current time).
        """
        params = b''
        params += int2byte(time.year - 2000)
        params += int2byte(time.month)
        params += int2byte(time.day)
        params += int2byte(time.hour)
        params += int2byte(time.minute)
        params += int2byte(time.second)
        self._send_command(Sportiduino.CMD_INIT_TIMECARD, params, wait_response=False)

    def init_passwd_card(self, old_passwd=0, new_passwd=0, flags=0):
        """Initialize card for writing new password to base station.
        @param old_passwd: Old password (default 0x000000).
        @param new_passwd: New password (default 0x000000).
        @param flags:      Flags byte (default 0x00).
        """
        params = b''
        params += Sportiduino._to_str(new_passwd, 3)
        params += Sportiduino._to_str(old_passwd, 3)
        params += Sportiduino._to_str(flags, 1)
        self._send_command(Sportiduino.CMD_INIT_PASSWDCARD, params, wait_response=False)

    def write_pages6_7(self, page6, page7):
        """Write additional pages."""
        params = b''
        params += page6[:5]
        params += page7[:5]
        self._send_command(Sportiduino.CMD_WRITE_PAGES6_7, params, wait_response=False)

    def enable_continuous_read(self):
        """Enable continuous card read."""
        self._set_mode(b'\x01')

    def disable_continuous_read(self):
        """Disable continuous card read."""
        self._set_mode(b'\x00')

    def _set_mode(self, mode):
        """Set master station read mode."""
        self._send_command(Sportiduino.CMD_SET_READ_MODE, mode, wait_response=False)

    def _connect_master_station(self, port):
        try:
            self._serial = Serial(port, baudrate=9600, timeout=5)
            # Master station reset on serial open.
            # Wait little time for it startup
            time.sleep(2)
        except (SerialException, OSError):
            raise SportiduinoException("Could not open port '%s'" % port)

        try:
            self._serial.reset_input_buffer()
        except (SerialException, OSError):
            raise SportiduinoException("Could not flush port '%s'" % port)

        self.port = port
        self.baudrate = self._serial.baudrate
        version = self.read_version()
        if version:
            self._log_info("Master station %s on port '%s' connected" % (version, port))

    def _send_command(self, code, parameters=None, wait_response=True, timeout=None):
        if parameters is None:
            parameters = b''
        data_len = len(parameters)
        if data_len > Sportiduino.MAX_DATA_LEN:
            raise SportiduinoException('Command too long: %d' % data_len)
        cmd_string = code + int2byte(data_len) + parameters

        cs = self._checsum(cmd_string)
        cmd = Sportiduino.START_BYTE + cmd_string + cs

        self._log_debug('=> %s' % ' '.join(hex(byte2int(c)) for c in cmd))

        self._serial.flushInput()
        self._serial.write(cmd)

        if wait_response:
            resp_code, data = self._read_response(timeout)
            return Sportiduino._preprocess_response(resp_code, data, self._log_debug)

        return None

    def _read_response(self, timeout=None, wait_fragment=None):
        try:
            if timeout:
                old_timeout = self._serial.timeout
                self._serial.timeout = timeout

            # Skip any bytes before START_BYTE
            while True:
                byte = self._serial.read()
                if byte == b'':
                    raise SportiduinoTimeout('No response')
                elif byte == Sportiduino.START_BYTE:
                    break

            if timeout:
                self._serial.timeout = old_timeout

            code = self._serial.read()
            length_byte = self._serial.read()
            length = byte2int(length_byte)

            more_fragments = False
            if length >= Sportiduino.OFFSET:
                more_fragments = True
                fragment_num = length - Sportiduino.OFFSET
                if fragment_num > 0 and (wait_fragment):
                    if fragment_num != wait_fragment:
                        raise SportiduinoException(
                            'Waiting fragment %d, receive %d'
                            % (wait_fragment, fragment_num)
                        )
                length = Sportiduino.MAX_DATA_LEN
            data = self._serial.read(length)
            checksum = self._serial.read()
            self._log_debug(
                "<= code '%s', len %i, data %s, cs %s"
                % (
                    hex(byte2int(code)),
                    length,
                    ' '.join(hex(byte2int(c)) for c in data),
                    hex(byte2int(checksum)),
                )
            )

            if not Sportiduino._cs_check(code + length_byte + data, checksum):
                raise SportiduinoException('Checksum mismatch')

        except (SerialException, OSError) as msg:
            raise SportiduinoException('Error reading response: %s' % msg)

        if more_fragments:
            next_code, next_data = self._read_response(timeout, fragment_num + 1)
            if next_code == code:
                data += next_data

        return code, data

    def __del__(self):
        if self._serial:
            self._serial.close()

    @staticmethod
    def _to_int(s):
        """Compute the integer value of a raw byte string (big endianes)."""
        value = 0
        for offset, c in enumerate(iterbytes(s[::-1])):
            value += c << offset * 8
        return value

    @staticmethod
    def _to_str(i, len):
        """
        @param i:   Integer to convert into str
        @param len: Length of the return value. If i does not fit OverflowError is raised.
        @return:    string representation of i (MSB first)
        """
        if PY3:
            return i.to_bytes(len, 'big')
        if i >> len * 8 != 0:
            raise OverflowError('%i too big to convert to %i bytes' % (i, len))
        string = b''
        for offset in range(len - 1, -1, -1):
            string += int2byte((i >> offset * 8) & 0xFF)
        return string

    @staticmethod
    def _preprocess_response(code, data, log_debug):
        if code == Sportiduino.RESP_ERROR:
            if data == Sportiduino.ERR_COM:
                raise SportiduinoException('COM error')
            elif data == Sportiduino.ERR_WRITE_CARD:
                raise SportiduinoException('Card write error')
            elif data == Sportiduino.ERR_READ_CARD:
                raise SportiduinoException('Card read error')
            elif data == Sportiduino.ERR_READ_EEPROM:
                raise SportiduinoException('EEPROM read error')
            else:
                raise SportiduinoException('Error with code %s' % hex(byte2int(code)))
        elif code == Sportiduino.RESP_OK:
            log_debug('Ok received')
        return code, data

    @staticmethod
    def _checsum(s):
        """Compute checksum of value.
        @param s: byte string
        """
        sum = 0
        for c in s:
            sum += byte2int(c)
        sum &= 0xFF
        return int2byte(sum)

    @staticmethod
    def _cs_check(s, checksum):
        return Sportiduino._checsum(s) == checksum

    @staticmethod
    def _parse_card_data(data):
        # TODO check data length
        ret = {}
        ret['card_number'] = Sportiduino._to_int(data[0:2])
        ret['page6'] = data[2:6]
        ret['page7'] = data[6:10]
        ret['punches'] = []
        for i in range(10, len(data), 5):
            cp = byte2int(data[i])
            time = datetime.fromtimestamp(Sportiduino._to_int(data[i + 1 : i + 5]))
            if cp == Sportiduino.START_STATION:
                ret['start'] = time
            elif cp == Sportiduino.FINISH_STATION:
                ret['finish'] = time
            else:
                ret['punches'].append((cp, time))

        return ret

    @staticmethod
    def _parse_card_raw_data(data):
        ret = {}
        for i in range(0, len(data), 5):
            page_num = byte2int(data[i])
            ret[page_num] = data[i + 1 : i + 5]

        return ret

    @staticmethod
    def _parse_backup(data):
        ret = {}
        cp = byte2int(data[0])
        ret['cp'] = cp
        ret['cards'] = []
        for i in range(1, len(data), 2):
            ret['cards'].append(Sportiduino._to_int(data[i : i + 2]))

        return ret


class SportiduinoException(Exception):
    pass


class SportiduinoTimeout(SportiduinoException):
    pass
