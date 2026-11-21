# !/usr/bin/python
# -*- coding:utf-8 -*-
"""Test script."""
# Python:   3.6.5+
# Platform: Windows/Linux/MacOS
# Author:   Heyn (heyunhuan@gmail.com)
# Program:  Test script.(Fast inventory)
# Package:  pip3 install pyImpinj.
# Drivers:  None.
# History:  2020-02-25 Ver:1.0 [Heyn] Initialization

import time
import queue
import logging

from sportorg.libs.rfid_impinj.pyImpinj import (
    ImpinjR2KReader,
    ImpinjR2KFastSwitchInventory,
)

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

    while True:
        try:
            data = TAG_QUEUE.get(timeout=0.1)
        except BaseException:
            R2000.fast_switch_ant_inventory(
                param=dict(
                    A=ImpinjR2KFastSwitchInventory.ANTENNA1,
                    Aloop=1,
                    B=ImpinjR2KFastSwitchInventory.ANTENNA2,
                    Bloop=1,
                    C=ImpinjR2KFastSwitchInventory.ANTENNA3,
                    Cloop=1,
                    D=ImpinjR2KFastSwitchInventory.ANTENNA4,
                    Dloop=1,
                    E=ImpinjR2KFastSwitchInventory.ANTENNA2,
                    Eloop=1,
                    F=ImpinjR2KFastSwitchInventory.ANTENNA3,
                    Floop=1,
                    G=ImpinjR2KFastSwitchInventory.ANTENNA4,
                    Gloop=1,
                    H=ImpinjR2KFastSwitchInventory.ANTENNA2,
                    Hloop=1,
                    Interval=0,
                    Repeat=1,
                )
            )
            continue
        print(data)


if __name__ == "__main__":
    main()
