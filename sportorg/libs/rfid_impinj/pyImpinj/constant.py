# !/usr/bin/python
# -*- coding:utf-8 -*-
"""Impinj R2000 constant."""
# Python:   3.6.5+
# Platform: Windows/Linux/MacOS
# Author:   Heyn (heyunhuan@gmail.com)
# Program:  Impinj R2000 protocol constant.
# Package:  None.
# Drivers:  None.
# History:  2020-02-18 Ver:1.0 [Heyn] Initialization

TAG_MEMORY_BANK = {"RESERVED": 0, "EPC": 1, "TID": 2, "USER": 3}

READER_ANTENNA = {
    "ANTENNA1": 0,
    "ANTENNA2": 1,
    "ANTENNA3": 2,
    "ANTENNA4": 3,
    "ANTENNA5": 4,
    "ANTENNA6": 5,
    "ANTENNA7": 6,
    "ANTENNA8": 7,
    "MAX": 8,
}

FREQUENCY_TABLES = [865 + (x * 0.5) for x in range(7)] + [
    902 + (x * 0.5) for x in range(53)
]
