# /usr/bin/env python
#
#    Copyright (C) 2018 Sergei Kobelev <kobelevsl@gmail.com>
#
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
#
#    Thanks to Alexander Kurdumov for test equipment
#    For more information about SFR please contact sfr-system@mail.ru <http://www.sportsystem.ru>
"""
sfrreader.py - Classes to read out SFR card data from master HID stations.
"""
import platform
from datetime import datetime
from time import sleep

if platform.system() == 'Windows':
    from pywinusb.hid import HidDevice, HidDeviceFilter


class SFRReader(object):
    SFR_DEBUG = False
    SFR_ALLOW_DUPLICATE = True  # Don't check card to be new, allow multiple reading of one card - used for debug only
    TIMEOUT_STEP = 0.001  # Sleeping step while waiting for command response
    TIMEOUT_LIMIT = 200  # Max count of sleeping calls

    # HID device properties
    VENDOR_ID = 0x2047
    PRODUCT_ID = 0x301

    HID_REPORT_COUNT = 64

    """Base protocol functions and constants to interact with SFR Stations."""

    # Protocol characters
    CMD_INIT = 0x3F
    CMD_START = 0xFD
    CMD_END = 0xFE

    CMD_REQUEST_CODE = 0x01
    CMD_BEEP_CODE = 0x03

    CMD_BEEP = [CMD_INIT, 0x05, CMD_START, CMD_BEEP_CODE, 0x01, 0x04, CMD_END]
    CMD_REQUEST = [CMD_INIT, 0x05, CMD_START, CMD_REQUEST_CODE, 0x01, 0x02, CMD_END]

    # SFR service codes
    CODE_START = 241
    CODE_FINISH = 240
    CODE_CHECK = 242

    def __init__(self, debug=False, logfile=None, logger=None):
        """Initializes communication with sfr station via HID interface.
        We have no information, how to manage 2 connected stations
        """
        self._device = None  # Type HidDevice
        self._debug = debug
        if logfile:
            self._logfile = open(logfile, 'ab')
        else:
            self._logfile = None
        self._logger = logger

        self._last_command = None
        self._last_card = None
        self._reading_process = False
        self._count = 0
        self._block = False
        self._is_card_connected = False
        self.ret = {}
        self.init_card_data()

        self._connect_reader()

    @staticmethod
    def check_sum(data):
        """Calculate the check sum for command
        Ported from C++ (ActiveX SFR component)
        """
        b1 = 0
        length = len(data)
        for i in range(length):
            csw = int(b1) + int(data[i])
            b1 = csw & 0xFF
            b1 += csw // 0x100
        return b1

    def get_hid_buffer(self, command):
        """Prepare 64 byte buffer for HidReport"""
        buffer = [0x00] * self.HID_REPORT_COUNT
        for i in range(len(command)):
            buffer[i] = command[i]
        return buffer

    def is_device_connected(self):
        if self._device and isinstance(self._device, HidDevice):
            if self._device.is_plugged() and self._device.is_opened():
                return True
        return False

    def _send_command(self, command, callback=True):
        """Send command to HID device"""
        if self.SFR_DEBUG:
            print("sfrreader.send_command: ==>> command '%s' " % command)

        buffer = self.get_hid_buffer(command)

        hid_device = self._device
        if self.is_device_connected():
            if callback:
                # Wait for the data response, callback is processed in HID data handler
                start = datetime.now()

                while self._block:
                    if self.SFR_DEBUG:
                        print('sfrreader.send_command: sleeping before command')
                    sleep(0.1)

                self._block = True
                self._last_command = command
                try:
                    hid_device.send_output_report(buffer)
                    count = 1
                    while self._block and count < self.TIMEOUT_LIMIT:
                        if self.SFR_DEBUG:
                            print(
                                'sfrreader.send_command: sleeping, waiting for response'
                            )
                        sleep(self.TIMEOUT_STEP)
                        count += 1

                    end = datetime.now()
                    time_used = end - start
                    if self.SFR_DEBUG:
                        print(
                            'sfrreader.send_command: ended in '
                            + str(time_used.microseconds / 1000)
                            + ' ms'
                        )
                except Exception as e:
                    if self.SFR_DEBUG:
                        print(
                            'sfrreader.send_command: device disconnected during command'
                        )
                    self._logger.error(str(e))
                    self.disconnect()

                self._block = False
            else:
                # Just send command
                hid_device.send_output_report(buffer)
                self._last_command = command
        else:
            if self.SFR_DEBUG:
                print('sfrreader.send_command: device is busy or unavailable')

    def _data_handler(self, data):
        if self.SFR_DEBUG:
            print('sfrreader.data_handler: Raw data: {0}'.format(data))

        last_command = self._last_command

        cmd_code = data[4]
        if not last_command or last_command[3] == data[3]:
            # correct answer, card detected

            if self._logger:
                self._logger.debug(
                    "sfrreader.data_handler ==>> command  '%s' " % last_command
                )
                self._logger.debug("sfrreader.data_handler <<== response '%s' " % data)

            self._is_card_connected = True
            if cmd_code == 1:
                # request of card id
                self._read_card_id(data)
            elif cmd_code == 3:
                # reading of bib
                self._read_bib(data)
            elif cmd_code == 4:
                # reading of counter
                self._read_data_counter(data)
            else:
                # reading of data
                self._read_data_punch(data)
        else:
            # no card connected
            self._is_card_connected = False

        self._block = False

    def request(self, pos=1, callback=True):
        command = SFRReader.CMD_REQUEST
        command[4] = pos
        command[5] = self.check_sum([self.CMD_REQUEST_CODE, pos])

        self._send_command(command, callback=callback)
        if self.SFR_DEBUG:
            print('sfrreader.request: end of request')

    def beep(self, count=1, delay=0.3):
        """Beep and blink control station. This even works if no card is
        inserted into the station.
        @param count: Count of beeps
        @param delay: Delay between beeps, don't use less than 0.3sec, it's ignored by device
        """

        # don't use less than 0.3sec, it's ignored by device
        if delay < 0.3:
            delay = 0.3

        command = SFRReader.CMD_BEEP

        for i in range(count):
            self._send_command(command, callback=False)
            sleep(delay)

    def ack_card(self):
        self.beep(delay=0.3, count=1)

    def disconnect(self):
        """Close the connection and disconnect from the station."""
        if self._device:
            self._device.close()

    def reconnect(self):
        """Close the connection and reopen again."""
        self.disconnect()
        self._connect_reader()

    def _read_card_id(self, data):
        self._last_card = data[5:9]

    def _read_bib(self, data):
        bib = int(data[5]) + int(data[6]) * 200 + int(data[7]) * 40000
        self.ret['bib'] = bib

    def _read_data_counter(self, data):
        # interesting, that counter shows less punches, then exist in card (e.g. counter = 10 for records 0 - 10)
        self._count = int(data[5]) + 1

    def _read_data_punch(self, data):
        code = int(data[5])
        time = self._decode_time(data[6:9])
        if code == self.CODE_START:
            self.ret['start'] = time
        elif code == self.CODE_CHECK:
            self.ret['check'] = time
        elif code == self.CODE_FINISH:
            self.ret['finish'] = time
        else:
            self.ret['punches'].append((code, time))

    def _connect_reader(self):
        """Connect to SFR Reader."""
        if platform.system() != 'Windows':
            raise SFRReaderException('Unsupported platform: %s' % platform.system())

        hid_filter = HidDeviceFilter(
            vendor_id=self.VENDOR_ID, product_id=self.PRODUCT_ID
        )
        devices = hid_filter.get_devices()

        if devices:
            device = devices[0]
            device.open()
            self._device = device

            self.beep(delay=0.3, count=3)

            if self._logger:
                self._logger.debug('SFR station connected')

            device.set_raw_data_handler(self._data_handler)
        else:
            if self._logger:
                self._logger.debug('SFR station not found or unavailable')

    def __del__(self):
        if self._device:
            self._device.close()

    @staticmethod
    def _decode_time(raw_time):
        """Decodes a raw time value read from an sfr card into a datetime object.
        The returned time is the nearest time matching the data before reftime."""
        if len(raw_time) > 2:
            h = int(raw_time[0]) // 16 * 10 + int(raw_time[0]) % 16
            m = int(raw_time[1]) // 16 * 10 + int(raw_time[1]) % 16
            s = int(raw_time[2]) // 16 * 10 + int(raw_time[2]) % 16

            if h > 23 or m > 59 or s > 59:
                return None

            now = datetime.now()
            ret = datetime(
                minute=m, second=s, hour=h, day=now.day, month=now.month, year=now.year
            )
            return ret
        return None

    def init_card_data(self):
        self.ret = {}
        self.ret['punches'] = []
        self.ret['card_type'] = 'SFR'
        self.ret['start'] = None
        self.ret['finish'] = None
        self.ret['check'] = None
        self.ret['card_number'] = 0

    def get_card_data(self):
        """Decodes a data record read from an SFR Card."""
        return self.ret


class SFRReaderReadout(SFRReader):
    """Class for SFR card readout. Reads out the card"""

    def __init__(self, *args, **kwargs):
        super(type(self), self).__init__(*args, **kwargs)
        self.last_card = None

    def poll_card(self):
        """Polls for an SFR-Card, located near the station (up to 5cm).
        Returns true on card detected and false otherwise."""

        if self._reading_process:
            return False

        if not (self.is_device_connected()):
            return False

        if self.SFR_ALLOW_DUPLICATE:
            self._last_card = None

        old_card = self._last_card
        self.request(1)

        return old_card != self._last_card

    def is_card_connected(self):
        return self._is_card_connected

    def read_card(self):
        """Reads out the SFR Card currently located near the station. The card must be
        detected with poll_card before."""
        if self._logger:
            self._logger.debug('reading of SFR card')

        self.init_card_data()

        self._reading_process = True
        i = 3
        self._count = 5  # will be overwritten in request(4)
        while i < self._count:

            self.request(i)  # see callback processing in data_handler method

            if not self.is_card_connected():  # card was removed during readout
                if self.SFR_DEBUG:
                    print(
                        'sfrreader.read_card: card was removed during readout, pos='
                        + str(i)
                    )
                self._last_card = None  # to allow rereading
                self._reading_process = False
                return

            i += 1
        self._reading_process = False
        return self.get_card_data()


class SFRReaderException(Exception):
    pass


class SFRReaderTimeout(Exception):
    pass


class SFRReaderCardChanged(Exception):
    pass
