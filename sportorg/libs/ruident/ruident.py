#!/usr/bin/env python
#
#    Copyright 2025 Ruident <sportidentsiberia@gmail.com>
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

"""ruident.py - Classes Ruident v1.1"""

from datetime import datetime
from os.path import exists, getmtime

from six import print_


class Ruident:
    def __init__(self, data_file="C:\\ruident\\data.csv", separator=";", debug=False, logger=None):
        self._serial = None
        self._logger = logger
        self._file_name = data_file
        self._separator = separator
        self._file = None
        self._last_update = None
        self._last_line = 0
        self._last_card = -1
        self.current_data = {}

        if debug:
            self._log_debug = print_

        if logger is not None:
            if callable(logger.debug):
                self._log_debug = logger.debug
            if callable(logger.info):
                self._log_info = logger.info

        if not exists(data_file):
            # no file
            raise FileNotFoundError(data_file)

        self._file = open(data_file)

    def get_next_data(self):
        self._logger.info("RUIDENT: get_next_data")
        cur_file_time = getmtime(self._file.name)
        if self._last_update != cur_file_time:
            self._logger.info(
                f"RUIDENT: get_next_data, file {self._file.name} was modified"
            )
            self._last_update = cur_file_time
            return self.read_file()
        return None

    def read_file(self):
        ret = list()
        lines = self._file.readlines()
        lines_count = len(lines)
        correct_lines = 0
        self._logger.info(f"RUIDENT: read_file, new lines: {lines_count}")
        if lines_count > 0:
            for i in range(0, lines_count):
                line = lines[i]
                self._logger.info(f"RUIDENT: read_file, processing line: {line}")
                separator = self._separator
                arr = line.split(separator)
                if len(arr) > 9:
                    correct_lines += 1
                    header = str(arr[0])
                    station_type = str(arr[1])
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
                        if self._last_card > 0 and correct_lines > 1:
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
                else:
                    self._logger.info(f"RUIDENT: read_file, ignoring line: {line}")
                    self._logger.info(
                        f"RUIDENT: correct format: @;type;code;HH;MM;SS;MS;card_id;battery;index)"
                    )
            ret.append(self.current_data)
        return ret

    def disconnect(self):
        self._file.close()
