#!/usr/bin/env python
#
#    Copyright 2025-2026 Ruident <sportidentsiberia@gmail.com>
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

"""ruident.py - Classes Ruident v0.6"""

import time
from datetime import datetime
import serial
from six import print_


class Ruident:
    def __init__(
        self, port="COM2", debug=False, logger=None, timeout_sec=0.1, baudrate=38400
    ):
        self._logger = logger
        self._logger.info(f"RUIDENT: creating reader for serial port {port}")
        self._serial = None
        self._port = port
        self._baudrate = baudrate
        self.current_data = {}
        self.timeout_sec = timeout_sec
        self.is_connected = False
        self._separator = ";"
        self._last_card = -1

        if debug:
            self._log_debug = print_

        if logger is not None:
            if callable(logger.debug):
                self._log_debug = logger.debug
            if callable(logger.info):
                self._log_info = logger.info

        self.connect()

    def connect(self):
        try:
            self._serial = serial.Serial(
                self._port, baudrate=self._baudrate, timeout=self.timeout_sec
            )
            time.sleep(1)
        except Exception as e:
            self._logger.exception(e)

    def read_data(self):
        ret = list()

        self._logger.info(f"RUIDENT: read data")

        skipped_lines = 0
        line = self._serial.readline()
        while line:
            separator = self._separator
            line_str = line.decode("utf-8").strip()
            arr = line_str.split(separator)

            if len(arr) < 10 or arr[0] != "@":
                self._logger.info(f"RUIDENT: read_file, ignoring line: {line_str}")
                self._logger.info(
                    f"RUIDENT: correct format: @;type;code;HH;MM;SS;MS;card_id;battery;index;date"
                )
                line = self._serial.readline()
                continue

            self._logger.info(f"RUIDENT: read_file, processing line: {line_str}")

            station_type = str(arr[1])

            header = str(arr[0])
            station_code = int(arr[2]) if arr[2] else 0
            h = int(arr[3])
            m = int(arr[4])
            s = int(arr[5])
            ms = int(arr[6])
            card_id = int(arr[7]) if arr[7] else 0
            battery = int(arr[8])
            index = int(arr[9])

            now = datetime.now()
            t = datetime(
                microsecond=ms * 1000,
                minute=m,
                second=s,
                hour=h,
                day=now.day,
                month=now.month,
                year=now.year,
            )

            if self._last_card != card_id:
                if self._last_card > 0:
                    # add object to return list if card was changed, skip existing card if no modification
                    ret.append(self.current_data.copy())
                self._last_card = card_id
                # create new card data object
                self.current_data = {"card_number": card_id, "punches": []}

            if station_type == "MR":
                self.current_data["punches"].append((station_code, t))
            elif station_type == "FR":
                self.current_data["finish"] = t
            elif station_type == "SR":
                self.current_data["start"] = t
            line = self._serial.readline()

        if self._last_card < 0:
            return None

        ret.append(self.current_data)
        self.current_data = {}
        self._last_card = -1
        return ret

    def disconnect(self):
        self._serial.close()
