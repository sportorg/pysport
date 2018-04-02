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
"""
sfrreader.py - Classes to read out SFR card data from master HID stations.
"""

from __future__ import print_function

from asyncio.tasks import sleep
from time import sleep

import datetime
from pywinusb.hid import HidDeviceFilter, HidDevice
from six import int2byte, byte2int, iterbytes, PY3

if PY3:
    # Make byte2int on Python 3.x compatible with
    # the fact that indexing into a byte variable
    # already returns an integer. With this byte2int(b[0])
    # works on 2.x and 3.x
    def byte2int(x):
        try:
            return x[0]
        except TypeError:
            return x

from serial.serialutil import SerialException
from datetime import datetime, timedelta
from binascii import hexlify
import os


class SFRReader(object):
    # HID device properties
    VENDOR_ID = 0x2047
    PRODUCT_ID = 0x301

    HID_REPORT_COUNT = 64

    """Base protocol functions and constants to interact with SFR Stations."""

    # Protocol characters

    CMD_INIT = 0x3f
    CMD_START = 0xfd
    CMD_END = 0xfe

    CMD_REQUEST_CODE = 0x01
    CMD_BEEP_CODE = 0x03

    CMD_BEEP = [CMD_INIT, 0x05, CMD_START, CMD_BEEP_CODE, 0x01, 0x04, CMD_END]
    CMD_REQUEST = [CMD_INIT, 0x05, CMD_START, CMD_REQUEST_CODE, 0x01, 0x02, CMD_END]

    def __init__(self, debug=False, logfile=None, logger=None):
        """Initializes communication with sfr station via HID interface.
            We have no information, how to manage 2 connected stations
        """
        self._device = None  # Type HidDevice
        self._debug = debug
        if logfile is not None:
            self._logfile = open(logfile, 'ab')
        else:
            self._logfile = None
        self._logger = logger
        self._last_command = None
        self._last_card = None
        self._reading_process = False
        self._count = 0
        self._block = False

        self._connect_reader()

    def check_sum(self, data, length):
        """Calculate the check sum for command
        Ported from C++ (ActiveX SFR component)
        """
        b1 = 0
        for i in range(length):
            csw = int(b1) + int(data[i])
            b1 = csw & 0xff
            b1 += csw // 0x100
        return b1

    def get_hid_buffer(self, command):
        """Prepare 64 byte buffer for HidReport"""
        buffer = [0x00] * self.HID_REPORT_COUNT
        for i in range(len(command)):
            buffer[i] = command[i]
        return buffer

    def _send_command(self, command, callback=True):
        """Send command to HID device"""
        if self._logger:
            self._logger.debug("==>> command '%s' " % command)
        print("==>> command '%s' " % command)

        buffer = self.get_hid_buffer(command)

        hid_device = self._device
        assert isinstance(hid_device, HidDevice)
        if hid_device.is_plugged() and hid_device.is_active():
            if callback:
                # Wait for the data response, callback is processed in HID data handler
                start = datetime.now()

                while (self._block):
                    sleep(0.000001)
                    # print('send_command: sleeping before command')

                self._block = True
                self._last_command = command
                hid_device.send_output_report(buffer)

                while (self._block):
                    sleep(0.000001)
                    # print('send_command: sleeping, waiting for response')

                end = datetime.now()
                time_used = end - start
                print('ended in ' + str(time_used.microseconds / 1000) + ' ms')

            else:
                # Just send command
                hid_device.send_output_report(buffer)
                self._last_command = command
        else:
            print('device is busy')

    def request(self, pos=1, callback=True):
        command = SFRReader.CMD_REQUEST
        command[4] = pos
        command[5] = self.check_sum([self.CMD_REQUEST_CODE, pos], 2)

        self._send_command(command, callback=callback)
        print('end of request')

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
        self.beep(delay=0.3)
        self._last_card = None

    def disconnect(self):
        """Close the connection an disconnect from the station."""
        if self._device:
            self._device.close()

    def reconnect(self):
        """Close the connection and reopen again."""
        self.disconnect()
        self._connect_reader()

    def _data_handler(self, data):
        print("Raw data: {0}".format(data))

        last_command = self._last_command
        if not last_command or last_command[3] == data[3]:
            # correct answer, card detected
            if data[4] == 1:
                # request of card id
                self._read_card_id(data)
            elif data[4] == 3:
                # reading of bib
                self._read_bib(data)
            elif data[4] == 4:
                # reading of counter
                self._read_data_counter(data)
            else:
                # reading of data
                self._read_data_punch(data)

        self._block = False

    def _read_card_id(self, data):
        self._last_card = data[5:9]

    def _read_bib(self, data):
        self._bib = int(data[5]) + int(data[6]) * 200 + int(data[7]) * 40000
        print('bib=' + str(self._bib))

    def _read_data_counter(self, data):
        self._count = int(data[5])

    def _read_data_punch(self, data):
        code = int(data[5])
        h = int(data[6]) // 16 * 10 + int(data[6]) % 16
        m = int(data[7]) // 16 * 10 + int(data[7]) % 16
        s = int(data[8]) // 16 * 10 + int(data[8]) % 16
        print ('code=' + str(code) + '  time=' + str(h) + ':' + str(m) + ':' + str(s))

    def _connect_reader(self):
        """Connect to SFR Reader.
        """
        filter = HidDeviceFilter(vendor_id=self.VENDOR_ID, product_id=self.PRODUCT_ID)
        devices = filter.get_devices()

        device = None
        if devices:
            device = devices[0]
            print("success")

            device.open()
            self._device = device

            device.set_raw_data_handler(self._data_handler)
        else:
            print("device not connected")


    def __del__(self):
        if self._device is not None:
            self._device.close()


    @staticmethod
    def _decode_time(raw_time, raw_ptd=None, reftime=None):
        """Decodes a raw time value read from an sfr card into a datetime object.
        The returned time is the nearest time matching the data before reftime."""
        if len(raw_time) > 3:
            h = int(raw_time[0]) // 16 * 10 + int(raw_time[0]) % 16
            m = int(raw_time[1]) // 16 * 10 + int(raw_time[1]) % 16
            s = int(raw_time[2]) // 16 * 10 + int(raw_time[2]) % 16
            ret = datetime.datetime()
            ret.second = s
            ret.minute = m
            ret.hour = h
            return ret

    @staticmethod
    def _append_punch(list, station, timedata):
        time = SFRReader._decode_time(timedata)
        if time is not None:
            list.append((station, time))

    @staticmethod
    def _decode_carddata(data, card_type, reftime=None):
        """Decodes a data record read from an SFR Card."""
        pass

class SFRReaderReadout(SFRReader):
    """Class for 'classic' SFR card readout. Reads out the whole card."""

    def __init__(self, *args, **kwargs):
        super(type(self), self).__init__(*args, **kwargs)

        self.last_card = None
        self.cardtype = None

    def poll_card(self):
        """Polls for an SFR-Card inserted or removed into the station.
        Returns true on state changes and false otherwise. If other commands
        are received an Exception is raised."""

        if self._reading_process:
            return False

        if not isinstance(self._device, HidDevice):
            return False

        if not self._device.is_plugged():
            return False

        oldcard = self._last_card
        self.request(1)

        print('compare: old=' + str(oldcard) + ' new=' + str(self._last_card))
        return not oldcard == self._last_card

    def read_card(self, reftime=None):
        """Reads out the SFR Card currently inserted into the station. The card must be
        detected with poll_card before."""
        self._logger.debug('reading of SFR card')
        self._reading_process = True
        self.request(3) # bib
        self.request(4) # count
        self.request(5) # just first record, can be empty
        i = 6
        if self._count:
            while i < self._count:
                self.request(i)
                i += 1
        self._reading_process = False

class SFRReaderException(Exception):
    pass


class SFRReaderTimeout(Exception):
    pass


class SFRReaderCardChanged(Exception):
    pass


# s = SFRReader()
#
# s.beep(1)
#
# for i in range(18):
#     s.request(i)
#
# s.beep(2)

# s = SFRReader()
# s.beep(1)
# s.request(1)
# sleep(2)
