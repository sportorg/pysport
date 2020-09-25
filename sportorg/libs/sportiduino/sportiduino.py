#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2018 - 2020 Semyon Yakimov <sdyakimov@gmail.com>
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

import os
import platform
import re
import time
from datetime import datetime, timedelta

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

    _translate = lambda _, s: s

    # Constants
    START_BYTE = b'\xFE'

    START_STATION = 240
    FINISH_STATION = 245
    CHECK_STATION = 248
    CLEAR_STATION = 249

    # Protocol commands
    CMD_INIT_TIMECARD = b'\x41'
    CMD_INIT_CP_NUM_CARD = b'\x42'
    CMD_INIT_PASSWDCARD = b'\x43'  # deprecated
    CMD_INIT_CARD = b'\x44'
    CMD_WRITE_PAGES6_7 = b'\x45'
    CMD_READ_VERS = b'\x46'
    CMD_INIT_BACKUPREADER = b'\x47'
    CMD_READ_BACKUPREADER = b'\x48'
    CMD_SET_READ_MODE = b'\x49'  # deprecated
    CMD_WRITE_SETTINGS = b'\x4a'
    CMD_READ_CARD = b'\x4b'
    CMD_READ_RAW = b'\x4c'
    CMD_READ_SETTINGS = b'\x4d'
    CMD_INIT_SLEEPCARD = b'\x4e'
    CMD_APPLY_PWD = b'\x4f'
    CMD_INIT_STATECARD = b'\x50'
    CMD_READ_CARD_TYPE = b'\x51'
    CMD_BEEP_ERROR = b'\x58'
    CMD_BEEP_OK = b'\x59'
    CMD_INIT_CONFIG_CARD = b'\x5a'

    # Protocol responses
    RESP_BACKUP = b'\x61'
    RESP_CARD_DATA = b'\x63'
    RESP_CARD_RAW = b'\x65'
    RESP_VERS = b'\x66'
    RESP_SETTINGS = b'\x67'
    RESP_MODE = b'\x69'  # deprecated
    RESP_CARD_TYPE = b'\x70'
    RESP_ERROR = b'\x78'
    RESP_OK = b'\x79'

    # Protocol error codes
    ERR_COM = b'\x01'
    ERR_WRITE_CARD = b'\x02'
    ERR_READ_CARD = b'\x03'
    ERR_READ_EEPROM = b'\x04'
    ERR_CARD_NOT_FOUND = b'\x05'
    ERR_UNKNOWN_CMD = b'\x06'

    MASTER_CARD_GET_STATE = b'\xF9'
    MASTER_CARD_SET_TIME = b'\xFA'
    MASTER_CARD_SET_NUMBER = b'\xFB'
    MASTER_CARD_SLEEP = b'\xFC'
    MASTER_CARD_READ_BACKUP = b'\xFD'
    MASTER_CARD_SET_PASS = b'\xFE'

    MIN_CARD_NUM = 1
    MAX_CARD_NUM = 65000

    class Version(object):
        """Sportiduino version."""

        def __init__(self, major, minor=None, patch=None):
            """Initializes version by bytes from master station.
            @param major, minor, patch: Bytes from master station.
            """

            if (
                (minor is None and patch is None) or minor == 0 and patch == 0
            ):  # old firmwares
                value = major
                if value >= 100 and value <= 104:  # v1.0 - v1.4
                    self.major = value // 100
                    self.minor = value % 100
                    self.patch = None
                else:
                    self.major = (value >> 6) + 1
                    self.minor = ((value >> 2) & 0x0F) + 1
                    self.patch = value & 0x03
                return

            self.major = major
            self.minor = minor
            self.patch = patch

        def __str__(self):
            """Override __str__ method.
            @return: User friendly version string.
            """
            vers_suffix = 'x'
            if self.patch is not None:
                vers_suffix = str(self.patch)
                max_patch_version = 239
                if self.patch > max_patch_version:
                    vers_suffix = '0-beta.%d' % (self.patch - max_patch_version)
            int(self.patch) if self.patch is not None else 'x'
            return 'v%d.%d.%s' % (self.major, self.minor, vers_suffix)

    class Config(object):
        def __init__(self, antenna_gain=0, timezone=0):
            self.antenna_gain = antenna_gain
            self.timezone = timezone

        @classmethod
        def unpack(cls, config_data):
            return cls(
                antenna_gain=byte2int(config_data[0]),
                timezone=timedelta(minutes=byte2int(config_data[1]) * 15),
            )

        def pack(self):
            config_data = b''
            config_data += int2byte(self.antenna_gain)
            print(self.timezone.total_seconds())
            config_data += int2byte(int(self.timezone.total_seconds() / 60 / 15))
            return config_data

    class SerialProtocol(object):
        OFFSET = 0x1E
        MAX_DATA_LEN = 28

        def __init__(self, start_byte, log_debug):
            self._start_byte = start_byte
            self._log_debug = log_debug

        def send_command(
            self, serial, code, parameters=None, wait_response=True, timeout=None
        ):
            if parameters is None:
                parameters = b''
            data_len = len(parameters)
            if data_len > self.MAX_DATA_LEN:
                raise SportiduinoException('Command too long: %d' % data_len)
            cmd_string = code + int2byte(data_len) + parameters

            cs = self._checsum(cmd_string)
            cmd = self._start_byte + cmd_string + cs

            self._log_debug('=> 0x %s' % ' '.join(('%02x' % byte2int(c)) for c in cmd))

            serial.flushInput()
            serial.write(cmd)

            if wait_response:
                return self._read_response(serial, timeout)

            return None, None

        def _read_response(self, serial, timeout=None, wait_fragment=None):
            try:
                if timeout is not None:
                    old_timeout = serial.timeout
                    serial.timeout = timeout

                # Skip any bytes before start byte
                while True:
                    byte = serial.read()
                    if byte == b'':
                        raise SportiduinoTimeout(
                            Sportiduino._translate('sportiduino', "No response")
                        )
                    elif byte == self._start_byte:
                        break

                if timeout is not None:
                    serial.timeout = old_timeout

                code = serial.read()
                length_byte = serial.read()
                length = byte2int(length_byte)

                more_fragments = False
                if length >= self.OFFSET:
                    more_fragments = True
                    fragment_num = length - self.OFFSET
                    if fragment_num > 0 and (wait_fragment is not None):
                        if fragment_num != wait_fragment:
                            raise SportiduinoException(
                                'Waiting fragment %d, receive %d'
                                % (wait_fragment, fragment_num)
                            )
                    length = self.MAX_DATA_LEN
                data = serial.read(length)
                checksum = serial.read()
                self._log_debug(
                    "<= code '%#02x', len %02i, data 0x %s, cs %#02x"
                    % (
                        byte2int(code),
                        length,
                        ' '.join(('%02x' % byte2int(c)) for c in data),
                        byte2int(checksum),
                    )
                )

                if not self._cs_check(code + length_byte + data, checksum):
                    raise SportiduinoException(
                        Sportiduino._translate('sportiduino', "Checksum mismatch")
                    )

            except (SerialException, OSError) as msg:
                raise SportiduinoException(
                    Sportiduino._translate(
                        'sportiduino', "Error reading response: {}"
                    ).format(msg)
                )

            if more_fragments:
                next_code, next_data = self._read_response(
                    serial, timeout, fragment_num + 1
                )
                if next_code == code:
                    data += next_data
                else:  # got an error
                    return next_code, next_data

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
            return Sportiduino.SerialProtocol._checsum(s) == checksum

    def __init__(self, port=None, debug=False, logger=None, translator=None):
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

        if translator is not None:
            Sportiduino._translate = translator

        self._serialproto = Sportiduino.SerialProtocol(
            Sportiduino.START_BYTE, self._log_debug
        )

        self.version = None

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
                scan_ports.sort(reverse=True)
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
            Sportiduino._translate(
                'sportiduino',
                "No Sportiduino master station found. Possible reasons: {}",
            ).format(errors)
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

    def read_version(self, timeout=None):
        """Read master station firmware version.
        @return: Version object.
        """
        code, data = self._send_command(Sportiduino.CMD_READ_VERS, timeout=timeout)
        if code == Sportiduino.RESP_VERS:
            data_len = len(data)
            if data_len == 3:
                return Sportiduino.Version(*data[0:3])
            else:  # old firmwares
                return Sportiduino.Version(data[0])
        return None

    def read_card_type(self):
        code, data = self._send_command(Sportiduino.CMD_READ_CARD_TYPE)
        if code == Sportiduino.RESP_CARD_TYPE:
            return data[0]
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
            raise SportiduinoException(
                Sportiduino._translate(
                    'sportiduino', "Unknown error during card reading"
                )
            )

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
            return self._parse_card_raw_data(data, self._log_debug)
        else:
            raise SportiduinoException('Read raw data failed')

    def read_backup(self):
        """Read backup from backupreader card.
        @return: Backup data in dictionary.
        """
        code, data = self._send_command(Sportiduino.CMD_READ_BACKUPREADER, timeout=1)
        if code == Sportiduino.RESP_BACKUP:
            return self._parse_backup(data)
        else:
            raise SportiduinoException('Read backup failed')

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
        return self._send_command(Sportiduino.CMD_INIT_CARD, params, wait_response=True)

    def init_backupreader(self):
        """Initialize backupreader card."""
        self._send_command(Sportiduino.CMD_INIT_BACKUPREADER, wait_response=True)

    def init_sleepcard(self, wakeuptime):
        """Initialize sleep card."""
        params = b''
        params += int2byte(wakeuptime.date().year() - 2000)
        params += int2byte(wakeuptime.date().month())
        params += int2byte(wakeuptime.date().day())
        params += int2byte(wakeuptime.time().hour())
        params += int2byte(wakeuptime.time().minute())
        params += int2byte(wakeuptime.time().second())
        self._send_command(Sportiduino.CMD_INIT_SLEEPCARD, params, wait_response=True)

    def init_cp_number_card(self, cp_number):
        """Initialize card for writing check point number to base station.
        @param cp_number: Check point number.
        """
        params = int2byte(cp_number)
        self._send_command(Sportiduino.CMD_INIT_CP_NUM_CARD, params, wait_response=True)

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
        self._send_command(Sportiduino.CMD_INIT_TIMECARD, params, wait_response=True)

    def init_config_card(self, bs_config_data):
        """Initialize card for writing configuration to base station."""
        self._send_command(
            Sportiduino.CMD_INIT_CONFIG_CARD, bs_config_data, wait_response=True
        )

    def init_state_card(self):
        params = b''
        self._send_command(Sportiduino.CMD_INIT_STATECARD, params, wait_response=True)

    def read_state_card(self):
        pageData = self.read_card_raw()

        if pageData[4][2] != 255 or pageData[4][1] != byte2int(
            Sportiduino.MASTER_CARD_GET_STATE
        ):
            raise SportiduinoException(
                Sportiduino._translate('sportiduino', "The state-card not found")
            )

        state = {}
        state['version'] = pageData[8][0:3]
        state['config'] = pageData[9]
        state['battery'] = byte2int(pageData[10][0])
        state['mode'] = byte2int(pageData[10][1])
        state['timestamp'] = datetime.fromtimestamp(
            Sportiduino._to_int(pageData[11][0:4])
        )
        state['wakeuptime'] = datetime.fromtimestamp(
            Sportiduino._to_int(pageData[12][0:4])
        )

        return state

    def apply_pwd(self, pwd=(0, 0, 0), flags=0):
        params = b''
        params += int2byte(pwd[0])
        params += int2byte(pwd[1])
        params += int2byte(pwd[2])
        params += int2byte(flags)
        self._send_command(Sportiduino.CMD_APPLY_PWD, params)

    def read_settings(self):
        code, data = self._send_command(Sportiduino.CMD_READ_SETTINGS)
        if code == Sportiduino.RESP_SETTINGS:
            return Sportiduino.Config.unpack(data)
        else:
            raise SportiduinoException("Read settings failed")

    def write_settings(self, antenna_gain, timezone):
        params = Sportiduino.Config(antenna_gain, timezone).pack()
        self._send_command(Sportiduino.CMD_WRITE_SETTINGS, params)

    def write_pages6_7(self, page6, page7):
        """Write additional pages."""
        params = b''
        params += page6[:5]
        params += page7[:5]
        self._send_command(Sportiduino.CMD_WRITE_PAGES6_7, params, wait_response=False)

    def enable_continuous_read(self):
        """Enable continuous card read. Deprecated."""
        self._set_mode(b'\x01')

    def disable_continuous_read(self):
        """Disable continuous card read. Deprecated"""
        self._set_mode(b'\x00')

    @staticmethod
    def card_name(card_type):
        if card_type == 1:
            return Sportiduino._translate(
                'sportiduino', "Compliant with ISO/IEC 14443-4"
            )
        elif card_type == 2:
            return Sportiduino._translate(
                'sportiduino', "Compliant with ISO/IEC 18092 (NFC)"
            )
        elif card_type == 3:
            return "MIFARE Classic Mini"
        elif card_type == 4:
            return "MIFARE Classic 1K"
        elif card_type == 5:
            return "MIFARE Classic 4K"
        elif card_type == 6:
            return "MIFARE Ultralight"
        elif card_type == 7:
            return "MIFARE Plus"
        elif card_type == 8:
            return "TNP3XXX"
        elif card_type == 9:
            return "NTAG213"
        elif card_type == 10:
            return "NTAG215"
        elif card_type == 11:
            return "NTAG216"
        elif card_type is None or card_type == 0 or card_type == 0xFF:
            return Sportiduino._translate('sportiduino', "Not detected")
        else:
            return Sportiduino._translate(
                'sportiduino', "Unknown card type: {}"
            ).format(card_type)

        return Sportiduino._translate('sportiduino', "Unknown type")

    def _set_mode(self, mode):
        """Set master station read mode. Deprecated."""
        self._send_command(Sportiduino.CMD_SET_READ_MODE, mode, wait_response=False)

    def _connect_master_station(self, port):
        try:
            self._serial = Serial(port, baudrate=38400, timeout=3)
        except (SerialException, OSError):
            raise SportiduinoException(
                Sportiduino._translate('sportiduino', "Could not open port {}").format(
                    port
                )
            )

        try:
            self._serial.reset_input_buffer()
        except (SerialException, OSError):
            raise SportiduinoException(
                Sportiduino._translate('sportiduino', "Could not flush port {}").format(
                    port
                )
            )

        # Master station with DTR connected resets on serial open.
        # It responds on the second attempt.
        for baudrate in (38400, 38400, 9600):
            try:
                self._serial.baudrate = baudrate
                self._log_debug(
                    "Try find master station on port '%s', baudrate %d"
                    % (port, self._serial.baudrate)
                )
                self.version = self.read_version(timeout=2)
            except SportiduinoTimeout:
                self._log_debug("No response")
            else:
                break

        if self.version is None:
            raise SportiduinoTimeout("No response")

        self.port = port
        self.baudrate = self._serial.baudrate
        self._log_info(
            "Master station %s on port '%s' at %d is connected"
            % (self.version, port, self.baudrate)
        )

    def _send_command(self, code, parameters=None, wait_response=True, timeout=None):
        resp_code, data = self._serialproto.send_command(
            self._serial, code, parameters, wait_response, timeout
        )
        return Sportiduino._preprocess_response(resp_code, data, self._log_debug)

    def __del__(self):
        if self._serial is not None:
            self._log_info("Disconnect master station")
            self._serial.close()

    @staticmethod
    def _to_int(s):
        """Compute the integer value of a raw byte string (big endianness)."""
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
    def _preprocess_response(func, data, log_debug):
        if func is None:
            return None

        err_code = int2byte(data[0])
        if func == Sportiduino.RESP_ERROR:

            card_type = data[1]
            card = Sportiduino.card_name(data[1])

            if err_code == Sportiduino.ERR_COM:
                raise SportiduinoException(
                    Sportiduino._translate('sportiduino', 'COM error')
                )
            elif err_code == Sportiduino.ERR_WRITE_CARD:
                raise SportiduinoException(
                    Sportiduino._translate(
                        'sportiduino', "Can't write the card ({})"
                    ).format(card)
                )
            elif err_code == Sportiduino.ERR_READ_CARD:
                raise SportiduinoException(
                    Sportiduino._translate(
                        'sportiduino', "Can't read the card ({})"
                    ).format(card)
                )
            elif err_code == Sportiduino.ERR_READ_EEPROM:
                raise SportiduinoException(
                    Sportiduino._translate('sportiduino', "Can't read EEPROM")
                )
            elif err_code == Sportiduino.ERR_CARD_NOT_FOUND:
                if card_type == 0 or card_type == 0xFF:
                    raise SportiduinoException(
                        Sportiduino._translate('sportiduino', 'Card is not found')
                    )
                else:
                    raise SportiduinoException(
                        Sportiduino._translate(
                            'sportiduino', 'Unsupported card type = {}'
                        ).format(card_type)
                    )
            elif err_code == Sportiduino.ERR_UNKNOWN_CMD:
                raise SportiduinoException(
                    Sportiduino._translate('sportiduino', 'Unknown command')
                )
            else:
                raise SportiduinoException(
                    Sportiduino._translate('sportiduino', 'Error code {}').format(
                        hex(byte2int(err_code))
                    )
                )
        elif func == Sportiduino.RESP_OK:
            log_debug('Ok received')

        return func, data

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
    def raw_data_to_card_data(data):
        ret = {}
        master_card_byte = byte2int(data[4][2])
        if master_card_byte == 0xFF:
            ret['master_card_flag'] = True
        ret['master_card_type'] = data[4][1]
        ret['card_number'] = Sportiduino._to_int(data[4][0:2])
        ret['init_timestamp'] = Sportiduino._to_int(data[5][0:4])
        ret['page6'] = data[6][0:4]
        ret['page7'] = data[7][0:4]
        ret['punches'] = []

        if 'master_card_flag' in ret:
            return ret

        init_time_low = Sportiduino._to_int(data[5][1:4])
        init_time_high = data[5][0]

        for page in data:
            if page < 8:
                continue

            cp = data[page][0]

            if cp == 0:
                continue

            cp_timestamp = 0
            cp_time_low = Sportiduino._to_int(data[page][1:4])

            if cp_time_low < init_time_low:
                cp_timestamp = ((init_time_high + 1) << 24) | cp_time_low
            else:
                cp_timestamp = (init_time_high << 24) | cp_time_low

            time = datetime.fromtimestamp(cp_timestamp)

            if cp == Sportiduino.START_STATION:
                ret['start'] = time
            elif cp == Sportiduino.FINISH_STATION:
                ret['finish'] = time
            else:
                ret['punches'].append((cp, time))

        return ret

    @staticmethod
    def _parse_card_raw_data(data, log_debug):
        ret = {}
        for i in range(0, len(data), 5):
            page_num = byte2int(data[i])
            ret[page_num] = data[i + 1 : i + 5]

        log_debug('Card raw data:')
        for p in ret:
            log_debug(
                '\tpage %02i: 0x %s'
                % (p, ' '.join('%02x' % byte2int(c) for c in ret[p]))
            )

        return ret

    @staticmethod
    def _parse_backup(data):
        if len(data) < 1:
            return None

        ret = {}
        ret['cp'] = byte2int(data[0])
        ret['cards'] = []

        if len(data) > 1:
            if data[1] == 0xFF:  # with timestamps
                for i in range(2, len(data), 6):
                    card_number = Sportiduino._to_int(data[i : i + 2])
                    time = datetime.fromtimestamp(
                        Sportiduino._to_int(data[i + 2 : i + 6])
                    )
                    ret['cards'].append((card_number, time))
            else:
                for i in range(1, len(data), 2):
                    ret['cards'].append(Sportiduino._to_int(data[i : i + 2]))

        return ret


class SportiduinoException(Exception):
    pass


class SportiduinoTimeout(SportiduinoException):
    pass
