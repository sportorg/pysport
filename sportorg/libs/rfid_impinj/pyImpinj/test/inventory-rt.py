# !/usr/bin/python
# -*- coding:utf-8 -*-
"""Test script."""
# Python:   3.6.5+
# Platform: Windows/Linux/MacOS
# Author:   Heyn (heyunhuan@gmail.com)
# Program:  Test script (Realtime inventory).
# Package:  pip3 install pyImpinj.
# Drivers:  None.
# History:  2020-02-25 Ver:1.0 [Heyn] Initialization

import time
import queue
import logging

from sportorg.libs.rfid_impinj.pyImpinj import ImpinjR2KReader, READER_ANTENNA

logging.basicConfig(level=logging.INFO)


def main():
    TAG_QUEUE = queue.Queue(1024)
    R2000 = ImpinjR2KReader(TAG_QUEUE, address=1)

    try:
        R2000.connect("COM9")
    except BaseException as err:
        print(err)
        return

    R2000.worker_start()
    R2000.fast_power(22)
    # print( R2000.get_rf_port_return_loss() )
    # print( R2000.get_ant_connection_detector() )
    # print( R2000.set_ant_connection_detector( 10 ) )

    antenna_array = [
        READER_ANTENNA["ANTENNA1"],
        READER_ANTENNA["ANTENNA2"],
        READER_ANTENNA["ANTENNA3"],
        READER_ANTENNA["ANTENNA4"],
        READER_ANTENNA["ANTENNA5"],
        READER_ANTENNA["ANTENNA6"],
        READER_ANTENNA["ANTENNA7"],
        READER_ANTENNA["ANTENNA8"],
    ]
    index = 0
    R2000.set_work_antenna(READER_ANTENNA["ANTENNA4"])
    while True:
        try:
            data = TAG_QUEUE.get(timeout=0.1)
        except BaseException:
            R2000.rt_inventory(repeat=10)
            continue

        if data["type"] == "DONE":
            index = index + 1
            index = 0 if index >= len(antenna_array) else index
            print(R2000.set_work_antenna(antenna_array[index]))

        print(data)


if __name__ == "__main__":
    main()
