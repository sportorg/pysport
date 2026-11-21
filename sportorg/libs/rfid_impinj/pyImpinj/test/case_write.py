# !/usr/bin/python
# -*- coding:utf-8 -*-
"""Test script."""
# Python:   3.6.5+
# Platform: Windows/Linux/MacOS
# Author:   Heyn (heyunhuan@gmail.com)
# Program:  Test script.
# Package:  None.
# Drivers:  None.
# History:  2020-02-20 Ver:1.0 [Heyn] Initialization

import time
import queue
import struct
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
    R2000.set_work_antenna(READER_ANTENNA["ANTENNA1"])

    while True:
        try:
            data = TAG_QUEUE.get(timeout=0.2)
        except BaseException:
            R2000.rt_inventory(repeat=1)
            continue

        time.sleep(1)
        print("EPC  --> {}".format(data["epc"]))
        USER_DATA = "00000000"
        print("[WRITE] Write {} to USER.".format(USER_DATA))
        R2000.write(data["epc"], data=USER_DATA, bank="USER")

        NEW_EPC = "646C8DBBD180000040000006"
        print("[WRITE] Change EPC {} to {}.".format(data["epc"], NEW_EPC))
        R2000.write(data["epc"], data=NEW_EPC, bank="EPC")


if __name__ == "__main__":
    main()
