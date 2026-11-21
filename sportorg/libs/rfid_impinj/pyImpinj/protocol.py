# !/usr/bin/python
# -*- coding:utf-8 -*-
"""Impinj R2000 module."""
# Python:   3.6.5+
# Platform: Windows/Linux/MacOS
# Author:   Heyn (heyunhuan@gmail.com)
# Program:  Impinj R2000 module protocol.
# Package:  pip install libscrc.
# Drivers:  None.
# History:  2020-02-17 Ver:1.0 [Heyn] Initialization
#           2020-02-19 Ver:1.1 [Heyn] New add some functions.
#           2020-02-20 Ver:1.1 [Heyn] New add get_rf_port_return_loss function.
#           2020-02-27 Ver:1.2 [Heyn] New add get(set)_frequency_region and get(set)_rf_link_profile

import logging

import libscrc

from .constant import TAG_MEMORY_BANK, READER_ANTENNA
from .enums import ImpinjR2KCommands
from .enums import ImpinjR2KFastSwitchInventory
from .enums import ImpinjR2KRegion


class ImpinjR2KProtocols(object):
    """
    R2000 = ImpinjR2KProtocols( )
    print( R2000.reset( ) )
    print( R2000.power( 20, 21, 20, 20 ) )
    print( R2000.work_antenna(0) )

    """

    def register(command):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                data = func(self, *args, **kwargs)
                data = [] if data is None else data
                message = [self.__head]
                message.extend([3 + len(data), self.__address, command])
                message.extend(data)
                message.append(libscrc.lrc(bytes(message)))
                self.__address = (
                    data[0]
                    if command == ImpinjR2KCommands.SET_READER_ADDRESS
                    else self.__address
                )
                logging.debug([hex(x) for x in message])

                if self.serial is not None:
                    try:
                        return self.serial.write(bytes(message))
                    except BaseException as err:
                        logging.error(err)
                return bytes(message)

            return wrapper

        return decorator

    def __init__(self, address=0xFF, serial=None):
        self.serial = serial
        self.__head, self.__address = 0xA0, address

    @register(ImpinjR2KCommands.RESET)
    def reset(self):
        pass

    @register(ImpinjR2KCommands.SET_UART_BAUDRATE)
    def baudrate(self, value=115200):
        """
        38400bps or 115200bps.
        """
        return [4 if value == 115200 else 3]

    @register(ImpinjR2KCommands.SET_READER_ADDRESS)
    def address(self, addr=0):
        assert 0 <= addr <= 254
        return [addr]

    @register(ImpinjR2KCommands.GET_FIRMWARE_VERSION)
    def version(self):
        pass

    @register(ImpinjR2KCommands.SET_WORK_ANTENNA)
    def set_work_antenna(self, antenna=READER_ANTENNA["ANTENNA1"]):
        """Set reader work antenna.
        @param      antenna(int) : 0 ~ 3
        """
        assert 0 <= antenna <= 7
        return [antenna]

    @register(ImpinjR2KCommands.GET_WORK_ANTENNA)
    def get_work_antenna(self):
        pass

    @register(ImpinjR2KCommands.SET_RF_POWER)
    def set_rf_power(
        self,
        ant1=0x00,
        ant2=0x00,
        ant3=0x00,
        ant4=0x00,
        ant5=0x00,
        ant6=0x00,
        ant7=0x00,
        ant8=0x00,
    ):
        assert (
            (0 <= ant1 <= 33)
            and (0 <= ant2 <= 33)
            and (0 <= ant3 <= 33)
            and (0 <= ant4 <= 33)
            and (0 <= ant5 <= 33)
            and (0 <= ant6 <= 33)
            and (0 <= ant7 <= 33)
            and (0 <= ant8 <= 33)
        )
        return [ant1, ant2, ant3, ant4, ant5, ant6, ant7, ant8]

    @register(ImpinjR2KCommands.GET_RF_POWER)
    def get_rf_power(self):
        pass

    @register(ImpinjR2KCommands.SET_TEMPORARY_OUTPUT_POWER)
    def fast_power(self, value=22):
        assert 22 <= value <= 33
        return [value]

    @register(ImpinjR2KCommands.SET_BEEPER_MODE)
    def beeper(self, mode=0):
        assert 0 <= mode <= 2
        return [mode]

    @register(ImpinjR2KCommands.GET_ANT_CONNECTION_DETECTOR)
    def get_ant_connection_detector(self):
        pass

    @register(ImpinjR2KCommands.SET_ANT_CONNECTION_DETECTOR)
    def set_ant_connection_detector(self, loss=0):
        """
        @param  loss = 0 # Disabled detector.
                loss (Unit:dB)
                (The higher the value, the higher the impedance matching requirements for the port)
        """
        return [loss]

    @register(ImpinjR2KCommands.SET_READER_IDENTIFIER)
    def set_reader_identifier(self, sn="0123456789AB"):
        data = [ord(x) for x in list(sn[0:12])]
        data.extend([0xFF] * (12 - len(data)))
        return data

    @register(ImpinjR2KCommands.GET_READER_IDENTIFIER)
    def get_reader_identifier(self):
        pass

    @register(ImpinjR2KCommands.INVENTORY)
    def inventory(self, repeat=0xFF):
        return [repeat]

    @register(ImpinjR2KCommands.GET_INVENTORY_BUFFER)
    def get_inventory_buffer(self):
        pass

    @register(ImpinjR2KCommands.GET_INVENTORY_BUFFER_TAG_COUNT)
    def get_inventory_buffer_tag_count(self):
        pass

    @register(ImpinjR2KCommands.GET_AND_RESET_INVENTORY_BUFFER)
    def get_and_reset_inventory_buffer(self):
        pass

    @register(ImpinjR2KCommands.RESET_INVENTORY_BUFFER)
    def reset_inventory_buffer(self):
        pass

    @register(ImpinjR2KCommands.REAL_TIME_INVENTORY)
    def rt_inventory(self, repeat=0xFF):
        return [repeat]

    @register(ImpinjR2KCommands.CUSTOMIZED_SESSION_TARGET_INVENTORY)
    def session_inventory(self, session="S1", target="A", repeat=1):
        sess = dict(S0=0, S1=1, S2=2, S3=3)
        return [sess.get(session, 1), 1 if target == "B" else 0, repeat]

    @register(ImpinjR2KCommands.FAST_SWITCH_ANT_INVENTORY)
    def fast_switch_ant_inventory(
        self,
        param=dict(
            A=ImpinjR2KFastSwitchInventory.ANTENNA1,
            Aloop=1,
            B=ImpinjR2KFastSwitchInventory.DISABLED,
            Bloop=1,
            C=ImpinjR2KFastSwitchInventory.DISABLED,
            Cloop=1,
            D=ImpinjR2KFastSwitchInventory.DISABLED,
            Dloop=1,
            E=ImpinjR2KFastSwitchInventory.ANTENNA1,
            Eloop=1,
            F=ImpinjR2KFastSwitchInventory.DISABLED,
            Floop=1,
            G=ImpinjR2KFastSwitchInventory.DISABLED,
            Gloop=1,
            H=ImpinjR2KFastSwitchInventory.DISABLED,
            Hloop=1,
            Interval=0,
            Repeat=1,
        ),
    ):
        """
        Interval : ( Unit : ms  )
        Repeat   : ( Uint : int )

        param = dict( A=ImpinjR2KFastSwitchInventory.ANTENNA1, Aloop=1,
                      B=ImpinjR2KFastSwitchInventory.ANTENNA2, Bloop=1,
                      C=ImpinjR2KFastSwitchInventory.ANTENNA3, Cloop=1,
                      D=ImpinjR2KFastSwitchInventory.DISABLED, Dloop=1,
                      Interval = 5,
                      Repeat   = 1 )
        """
        return [
            param.get("A", ImpinjR2KFastSwitchInventory.DISABLED),
            param.get("Aloop", 1),
            param.get("B", ImpinjR2KFastSwitchInventory.DISABLED),
            param.get("Bloop", 1),
            param.get("C", ImpinjR2KFastSwitchInventory.DISABLED),
            param.get("Cloop", 1),
            param.get("D", ImpinjR2KFastSwitchInventory.DISABLED),
            param.get("Dloop", 1),
            param.get("E", ImpinjR2KFastSwitchInventory.DISABLED),
            param.get("Eloop", 1),
            param.get("F", ImpinjR2KFastSwitchInventory.DISABLED),
            param.get("Floop", 1),
            param.get("G", ImpinjR2KFastSwitchInventory.DISABLED),
            param.get("Gloop", 1),
            param.get("H", ImpinjR2KFastSwitchInventory.DISABLED),
            param.get("Hloop", 1),
            param.get("Interval", 5),
            param.get("Repeat", 1),
        ]

    def gpio(self, port, level=False):
        """
        ONLY [R] : GPIO1 and GPIO2
        ONLY [W] : GPIO3 and GPIO4

        e.g:
            R2000 = ImpinjR2KProtocols( )
            print( R2000.gpio( 1 ) )
        """
        assert 1 <= port <= 4
        if 3 <= port <= 4:
            ret = ImpinjR2KProtocols.register(ImpinjR2KCommands.SET_GPIO_VALUE)(
                lambda x, y: y
            )(self, [port, 0x01 if level else 0x00])
        else:
            ret = ImpinjR2KProtocols.register(ImpinjR2KCommands.GET_GPIO_VALUE)(
                lambda x, y: y
            )(self, [])
        return ret

    @register(ImpinjR2KCommands.GET_READER_TEMPERATURE)
    def temperature(self):
        pass

    @register(ImpinjR2KCommands.READ)
    def read(self, bank="EPC", addr=0, size=2, password=[0] * 4):
        body = []
        body.extend([TAG_MEMORY_BANK.get(bank, 1), addr, size])
        body.extend(password)
        return body

    @register(ImpinjR2KCommands.WRITE)
    def write(self, data: list, bank="EPC", addr=0, password=[0] * 4):
        body = []
        body.extend(password)
        body.append(TAG_MEMORY_BANK.get(bank, 1))
        body.append(2 if ((bank == "EPC") and (addr == 0)) else addr)
        body.append(len(data) // 2)
        body.extend(data)
        return body

    @register(ImpinjR2KCommands.WRITE_BLOCK)
    def write_block(self, data: list, bank="EPC", addr=0, password=[0] * 4):
        body = []
        body.extend(password)
        body.append(TAG_MEMORY_BANK.get(bank, 1))
        body.append(2 if ((bank == "EPC") and (addr == 0)) else addr)
        body.append(len(data) // 2)
        body.extend(data)
        return body

    @register(ImpinjR2KCommands.LOCK)
    def lock(self, bank="EPC", lock_type="OPEN", password=[0] * 4):
        """
        @param
            bank      = [ 'USER', 'TID', 'EPC', 'ACCESS_PASSWORD', 'KILL_PASSWORD' ]
            lock_type = [ 'OPEN', 'LOCK', 'OPEN_FOREVER', 'LOCK_FOREVER' ]
        """
        assert type(password) is list
        membank = dict(USER=1, TID=2, EPC=3, ACCESS_PASSWORD=4, KILL_PASSWORD=5)
        locktype = dict(OPEN=0, LOCK=1, OPEN_FOREVER=2, LOCK_FOREVER=3)
        body = []
        body.extend(password)
        body.append(membank.get(bank, 1))
        body.append(locktype.get(lock_type, 1))
        return body

    @register(ImpinjR2KCommands.KILL)
    def kill(self, password=[0] * 4):
        assert type(password) is list
        return password

    @register(ImpinjR2KCommands.SET_ACCESS_EPC_MATCH)
    def set_access_epc_match(self, mode, epc: list):
        assert mode in (0, 1)
        body = [mode, len(epc)]
        body.extend(epc)
        return body

    @register(ImpinjR2KCommands.GET_ACCESS_EPC_MATCH)
    def get_access_epc_match(self):
        pass

    @register(ImpinjR2KCommands.GET_RF_PORT_RETURN_LOSS)
    def get_rf_port_return_loss(self, param):
        return [param]

    @register(ImpinjR2KCommands.SET_FREQUENCY_REGION)
    def set_frequency_region(self, region, start, stop):
        return [region, start, stop]

    @register(ImpinjR2KCommands.GET_FREQUENCY_REGION)
    def get_frequency_region(self):
        pass

    @register(ImpinjR2KCommands.SET_FREQUENCY_REGION)
    def set_frequency_region_user(self, start, space, quantity):
        """
        start : e.g. 915000KHz --> 0D F6 38 (unit KHz)
        space : space*10 (unit KHz)
        quantity : must be above 0
        """
        assert quantity > 0
        body = [ImpinjR2KRegion.USER, space * 10, quantity]
        body.append(((start & 0x00FF0000) >> 16) & 0x000000FF)
        body.append(((start & 0x0000FF00) >> 8) & 0x000000FF)
        body.append(((start & 0x000000FF) >> 0) & 0x000000FF)
        return body

    @register(ImpinjR2KCommands.SET_RF_LINK_PROFILE)
    def set_rf_link_profile(self, profile_id):
        return [profile_id]

    @register(ImpinjR2KCommands.GET_RF_LINK_PROFILE)
    def get_rf_link_profile(self):
        pass

    @register(ImpinjR2KCommands.ISO18000_6B_INVENTORY)
    def iso1800_6b_inventory(self):
        """ISO 18000 - 6B"""
        pass
