# !/usr/bin/python
# -*- coding:utf-8 -*-
"""Impinj R2000 ENUMS."""
# Python:   3.6.5+
# Platform: Windows/Linux/MacOS
# Author:   Heyn (heyunhuan@gmail.com)
# Program:  Impinj R2000 ENUMS.
# Package:  None.
# Drivers:  None.
# History:  2020-02-18 Ver:1.0 [Heyn] Initialization.
#           2020-02-27 Ver:1.2 [Heyn] New add ImpinjR2KRegion and ImpinjR2KRFLinkProfile.
#           2020-03-03 Ver:1.2 Encoding UTF-8

import logging


class ImpinjR2KFastSwitchInventory(object):
    ANTENNA1 = 0
    ANTENNA2 = 1
    ANTENNA3 = 2
    ANTENNA4 = 3
    ANTENNA5 = 4
    ANTENNA6 = 5
    ANTENNA7 = 6
    ANTENNA8 = 7
    DISABLED = 0xFF


class ImpinjR2KCommands(object):
    GET_GPIO_VALUE = 0x60
    SET_GPIO_VALUE = 0x61
    SET_ANT_CONNECTION_DETECTOR = 0x62
    GET_ANT_CONNECTION_DETECTOR = 0x63
    SET_TEMPORARY_OUTPUT_POWER = 0x66
    SET_READER_IDENTIFIER = 0x67
    GET_READER_IDENTIFIER = 0x68
    SET_RF_LINK_PROFILE = 0x69
    GET_RF_LINK_PROFILE = 0x6A

    RESET = 0x70
    SET_UART_BAUDRATE = 0x71
    GET_FIRMWARE_VERSION = 0x72
    SET_READER_ADDRESS = 0x73
    SET_WORK_ANTENNA = 0x74
    GET_WORK_ANTENNA = 0x75
    SET_RF_POWER = 0x76
    GET_RF_POWER = 0x77
    SET_FREQUENCY_REGION = 0x78
    GET_FREQUENCY_REGION = 0x79
    SET_BEEPER_MODE = 0x7A
    GET_READER_TEMPERATURE = 0x7B
    GET_RF_PORT_RETURN_LOSS = 0x7E

    ### 18000-6C
    INVENTORY = 0x80
    READ = 0x81
    WRITE = 0x82
    LOCK = 0x83
    KILL = 0x84
    SET_ACCESS_EPC_MATCH = 0x85
    GET_ACCESS_EPC_MATCH = 0x86

    REAL_TIME_INVENTORY = 0x89
    FAST_SWITCH_ANT_INVENTORY = 0x8A
    CUSTOMIZED_SESSION_TARGET_INVENTORY = 0x8B
    SET_IMPINJ_FAST_TID = 0x8C
    SET_AND_SAVE_IMPINJ_FAST_TID = 0x8D
    GET_IMPINJ_FAST_TID = 0x8E

    ### ISO18000-6B
    ISO18000_6B_INVENTORY = 0xB0
    ISO18000_6B_READ = 0xB1
    ISO18000_6B_WRITE = 0xB2
    ISO18000_6B_LOCK = 0xB3
    ISO18000_6B_QUERY_LOCK = 0xB4

    GET_INVENTORY_BUFFER = 0x90
    GET_AND_RESET_INVENTORY_BUFFER = 0x91
    GET_INVENTORY_BUFFER_TAG_COUNT = 0x92
    RESET_INVENTORY_BUFFER = 0x93

    WRITE_BLOCK = 0x94


class ImpinjR2KGlobalErrors(object):
    SUCCESS = 0x10
    FAIL = 0x11

    MCU_RESET_ERROR = 0x20
    CW_ON_ERROR = 0x21
    ANTENNA_MISSING_ERROR = 0x22
    WRITE_FLASH_ERROR = 0x23
    READ_FLASH_ERROR = 0x24
    SET_OUTPUT_POWER_ERROR = 0x25

    TAG_INVENTORY_ERROR = 0x31
    TAG_READ_ERROR = 0x32
    TAG_WRITE_ERROR = 0x33
    TAG_LOCK_ERROR = 0x34
    TAG_KILL_ERROR = 0x35
    NO_TAG_ERROR = 0x36
    INVENTORY_OK_BUT_ACCESS_FAIL = 0x37
    BUFFER_IS_EMPTY_ERROR = 0x38
    NXP_CUSTOM_COMMAND_FAIL = 0x3C

    ACCESS_OR_PASSWORD_ERROR = 0x40
    PARAMETER_INVALID = 0x41
    PARAMETER_INVALID_WORDCNT_TOO_LONG = 0x42
    PARAMETER_INVALID_MEMBANK_OUT_OF_RANGE = 0x43
    PARAMETER_INVALID_LOCK_REGION_OUT_OF_RANGE = 0x44
    PARAMETER_INVALID_LOCK_ACTION_OUT_OF_RANGE = 0x45
    PARAMETER_READER_ADDRESS_INVALID = 0x46
    PARAMETER_INVALID_ANTENNA_ID_OUT_OF_RANGE = 0x47
    PARAMETER_INVALID_OUTPUT_POWER_OUT_OF_RANGE = 0x48
    PARAMETER_INVALID_FREQUENCY_REGION_OUT_OF_RANGE = 0x49
    PARAMETER_INVALID_BAUDRATE_OUT_OF_RANGE = 0x4A
    PARAMETER_BEEPER_MODE_OUT_OF_RANGE = 0x4B
    PARAMETER_EPC_MATCH_LEN_TOO_LONG = 0x4C
    PARAMETER_EPC_MATCH_LEN_ERROR = 0x4D
    PARAMETER_INVALID_EPC_MATCH_MODE = 0x4E
    PARAMETER_INVALID_FREQUENCY_RANGE = 0x4F

    FAIL_TO_GET_RN16_FROM_TAG = 0x50
    PARAMETER_INVALID_DRM_MODE = 0x51
    PLL_LOCK_FAIL = 0x52
    RF_CHIP_FAIL_TO_RESPONSE = 0x53
    FAIL_TO_ACHIEVE_DESIRED_OUTPUT_POWER = 0x54
    COPYRIGHT_AUTHENTICATION_FAIL = 0x55
    SPECTRUM_REGULATION_ERROR = 0x56
    OUTPUT_POWER_TOO_LOW = 0x57
    FAIL_TO_GET_RF_PORT_RETURN_LOSS = 0xEE

    @classmethod
    def to_string(cls, error_code):
        if error_code == cls.MCU_RESET_ERROR:
            return "MCU reset error."
        elif error_code == cls.WRITE_FLASH_ERROR:
            return "Write flash error."

        ### 0x2*
        elif error_code == cls.ANTENNA_MISSING_ERROR:
            return "Antenna miss error."
        elif error_code == cls.SET_OUTPUT_POWER_ERROR:
            return "Set output power error."

        ### 0x3*
        elif error_code == cls.TAG_INVENTORY_ERROR:
            return "Tag inventory error"
        elif error_code == cls.TAG_READ_ERROR:
            return "Tag read error"
        elif error_code == cls.TAG_WRITE_ERROR:
            return "Tag write error"
        elif error_code == cls.TAG_LOCK_ERROR:
            return "Tag lock error"
        elif error_code == cls.TAG_KILL_ERROR:
            return "Tag kill error"
        elif error_code == cls.NO_TAG_ERROR:
            return "No tag error"
        elif error_code == cls.INVENTORY_OK_BUT_ACCESS_FAIL:
            return "Inventory is ok, but access failed."
        elif error_code == cls.BUFFER_IS_EMPTY_ERROR:
            return "Buffer is empty."
        elif error_code == cls.NXP_CUSTOM_COMMAND_FAIL:
            return "NXP command failed."

        return "SUCCESS"


class ImpinjR2KMemoryBank(object):
    RESERVED = 0
    EPC = 1
    TID = 2
    USER = 3


class ImpinjR2KRegion(object):
    FCC = 1
    ETSI = 2
    CHN = 3
    USER = 4


class ImpinjR2KRFLinkProfile(object):
    PROFILE0 = 0xD0  # Tari 25uS,FM0 40KHz
    PROFILE1 = 0xD1  # Tari 25uS,Miller 4 250KHz ( Default )
    PROFILE2 = 0xD2  # Tari 25uS,Miller 4 300KHz
    PROFILE3 = 0xD3  # Tari 6.25uS,FM0 400KHz
