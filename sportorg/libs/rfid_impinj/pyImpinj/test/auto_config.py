# !/usr/bin/python
# -*- coding:utf-8 -*-
"""Test script."""
# Python:   3.6.5+
# Platform: Windows/Linux/MacOS
# Author:   Heyn (heyunhuan@gmail.com)
# Program:  Test script( Auto Config ).
# Package:  pip3 install pyImpinj.
# Drivers:  None.
# History:  2020-02-27 Ver:1.0 [Heyn] Initialization

import time
import queue
import logging

from sportorg.libs.rfid_impinj.pyImpinj import (
    ImpinjR2KReader,
    READER_ANTENNA,
    FREQUENCY_TABLES,
)

logging.basicConfig(level=logging.ERROR)


def main():
    TAG_QUEUE = queue.Queue(1024)
    R2000 = ImpinjR2KReader(TAG_QUEUE, address=1)

    try:
        R2000.connect("COM9")
    except BaseException as err:
        print(err)
        return

    R2000.worker_start()
    R2000.fast_power(30)
    # print( R2000.set_frequency_region( start=905, stop=911.3 ) )
    # print( R2000.get_frequency_region( ) )
    time.sleep(1)
    R2000.set_work_antenna(READER_ANTENNA["ANTENNA4"])
    for freq in FREQUENCY_TABLES[6:]:
        print(
            "FREQ {} -> RL:{}db".format(freq, R2000.get_rf_port_return_loss(freq=freq))
        )


if __name__ == "__main__":
    main()
