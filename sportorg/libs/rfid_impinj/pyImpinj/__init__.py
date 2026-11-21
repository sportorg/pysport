# !/usr/bin/python
# -*- coding:utf-8 -*-
"""Library for Impinj R2000 module."""
# Python:   3.6.5+
# Platform: Windows/Linux/MacOS
# Author:   Heyn (heyunhuan@gmail.com)
# Program:  Library for Impinj R2000 module.
# Package:  pip3 install liscrc pyserial
# Drivers:  None.
# History:  2020-02-18 Ver:1.0 [Heyn] Initialization
#           2020-02-20 Ver:1.1 [Heyn] New add read & write & get_rf_port_return_loss function.
#           2020-02-24 Ver:1.1 [Heyn] Bugfix:20200224
#           2020-02-27 Ver:1.2 [Heyn] New add get(set)_frequency_region
#           2020-03-02 Ver:1.2 [Heyn] Bugfix:20200302 The last message was not processed.
#           2020-03-03 Ver:1.2 [Heyn] Optimize the code.
#           2020-03-04 Ver:1.3 [Heyn] New add distance function.

__author__ = "Heyn"
__version__ = "1.3"

import logging
import os
import queue
import struct

import libscrc
import serial
import serial.threaded
import serial.tools.list_ports

from .constant import FREQUENCY_TABLES, READER_ANTENNA
from .enums import ImpinjR2KCommands
from .enums import ImpinjR2KFastSwitchInventory
from .enums import ImpinjR2KGlobalErrors
from .enums import ImpinjR2KRegion
from .protocol import ImpinjR2KProtocols


class ImpinjProtocolFactory(serial.threaded.FramedPacket):
    START = b"\xa0"

    def __init__(self, package_queue, command_queue, address=0xFF):
        self.packet = bytearray()
        self.in_packet = False
        self.transport = None
        self.address = address
        self.package_queue = package_queue
        self.command_queue = command_queue
        super(ImpinjProtocolFactory, self).__init__()

    def __call__(self):
        return self

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        # logging.debug( data )
        for byte in serial.iterbytes(data):
            if (byte == self.START) and (self.in_packet is False):
                self.in_packet = True
                self.packet.extend(byte)
            elif self.in_packet:
                self.packet.extend(byte)

                if (self.packet[1] + 2) == len(self.packet):
                    self.in_packet = False
                    if (
                        self.address == self.packet[2]
                    ):  # Check if the address is correct.
                        if (
                            libscrc.lrc(bytes(self.packet)) == 0
                        ):  # Check if the package's crc is correct.
                            self.handle_packet(bytes(self.packet))  # Process data.
                    del self.packet[:]  # Clear buffer.

    def handle_packet(self, packet):
        try:
            length, command, message = packet[1], packet[3], packet[4:-1]
        except BaseException as err:
            logging.error(
                "[ERROR] ImpinjProtocolFactory.handle_packet : {}".format(err)
            )
            return
        ### Tags
        if command in [
            ImpinjR2KCommands.REAL_TIME_INVENTORY,
            ImpinjR2KCommands.ISO18000_6B_INVENTORY,
            ImpinjR2KCommands.FAST_SWITCH_ANT_INVENTORY,
            ImpinjR2KCommands.CUSTOMIZED_SESSION_TARGET_INVENTORY,
        ]:
            if len(message) <= 1:
                self.package_queue.put(
                    dict(type="ERROR", logs=ImpinjR2KGlobalErrors.to_string(message[0]))
                )
                return

            ### Special process.
            if length == 0x0A:  # Operation successful.
                if command in [
                    ImpinjR2KCommands.REAL_TIME_INVENTORY,
                    ImpinjR2KCommands.CUSTOMIZED_SESSION_TARGET_INVENTORY,
                ]:
                    ### Head -- Length(fix=0x0A) -- Address -- Cmd -- AntID(1B) -- ReadRate(2B) -- TotalRead(4B) -- Check
                    duration = struct.unpack(">H", message[1:3])[0]
                    total_read = struct.unpack(">I", message[3:7])[0]
                else:
                    ### Head -- Length(fix=0x0A) -- Address -- Cmd -- TotalRead(3B) -- CommandDuration(4B) -- Check
                    total_read = (
                        ((message[0] << 16) & 0x00FF0000)
                        + ((message[1] << 8) & 0x0000FF00)
                        + message[2]
                    )
                    duration = struct.unpack(">I", message[3:7])[0]
                self.package_queue.put(
                    dict(type="DONE", total_read=total_read, duration=duration)
                )
                return

            elif length == 0x04:  # Operation failed.
                ### Head -- Length(fix=0x04) -- Address -- Cmd -- ErrorCode -- Check
                self.package_queue.put(
                    dict(
                        type="ERROR",
                        logs="{}".format(ImpinjR2KGlobalErrors.to_string(message[0])),
                    )
                )
                return

            antenna = (message[0] & 0x03) + 1
            frequency = FREQUENCY_TABLES[(((message[0] & 0xFC) >> 2) & 0x3F)]

            try:
                pc = struct.unpack(">H", message[1:3])[0]
            except BaseException:
                if message[1] == ImpinjR2KGlobalErrors.ANTENNA_MISSING_ERROR:
                    self.package_queue.put(
                        dict(
                            type="ERROR", logs="Antenna-{} disconnect.".format(antenna)
                        )
                    )
                return

            size = ((pc & 0xF800) >> 10) & 0x003E
            if size == 0:
                self.package_queue.put(dict(type="ERROR", logs="Nothing!"))
                return

            rssi = message[-1] - 129
            epc = "".join(
                ["%02X" % x for x in message[3 : size + 3]]
            )  # Bugfix:20200224
            self.package_queue.put(
                dict(
                    type="TAG", antenna=antenna, frequency=frequency, rssi=rssi, epc=epc
                )
            )
        else:
            self.command_queue.put(dict(command=command, data=message))

    def connection_lost(self, exc):
        self.transport = None
        logging.debug("[ERROR] Serial port connection lost.")
        super(ImpinjProtocolFactory, self).connection_lost(exc)


class ImpinjR2KReader(object):
    def catch_exception(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except BaseException as err:
                logging.error(str(err))
                return 0

        return wrapper

    def analyze_data(method="RESULT", timeout=3):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                func(self, *args, **kwargs)
                try:
                    data = self.command_queue.get(timeout=timeout)
                    if method == "DATA":
                        return data["data"]
                    else:
                        return (
                            True
                            if data["data"][0] == ImpinjR2KGlobalErrors.SUCCESS
                            else False,
                            ImpinjR2KGlobalErrors.to_string(data["data"][0]),
                        )
                except BaseException as err:
                    logging.error(
                        "[ERROR] ANALYZE_DATA error {} or COMMAND QUEUE is timeout.".format(
                            err
                        )
                    )
                    return bytes([ImpinjR2KGlobalErrors.FAIL])

            return wrapper

        return decorator

    def __init__(self, package_queue, address=0xFF):
        self.package_queue, self.address = package_queue, address
        self.command_queue = queue.Queue(1024)
        self.ser, self.serial_worker = None, None
        super(ImpinjR2KReader, self).__init__()

    def __del__(self):
        self.worker_close()

    def scan_serial_port(self, description="COM"):
        """
        device[0] : COMxx
        device[1] : Prolific USB-to-Serial Comm Port (COMxx)
        device[2] : USB VID:PID=067B:2303 SER=6 LOCATION=1-1.1
        """
        for device in list(serial.tools.list_ports.comports()):
            if description in device[1]:
                yield device[0]

    def connect(self, port="COM1", baudrate=115200):
        self.ser = serial.serial_for_url(port, do_not_open=True)
        self.ser.baudrate, self.ser.bytesize = baudrate, 8
        self.ser.parity, self.ser.stopbits = serial.PARITY_NONE, serial.STOPBITS_ONE

        try:
            self.ser.open()
            if os.name == "nt":  # sys.platform == 'win32':
                self.ser.set_buffer_size(1024 * 10)
        except BaseException as err:
            raise FileNotFoundError(
                "Could not open serial port {}: {}".format(self.ser.name, err)
            )

        self.protocol = ImpinjR2KProtocols(address=self.address, serial=self.ser)

        return True

    def worker_start(self):
        self.protocol_factory = ImpinjProtocolFactory(
            self.package_queue, self.command_queue, self.address
        )
        self.serial_worker = serial.threaded.ReaderThread(
            self.ser, self.protocol_factory
        )
        self.serial_worker.start()

    def worker_close(self):
        if self.serial_worker:
            self.serial_worker.close()
        self.serial_worker = None

    # -------------------------------------------------

    @analyze_data("DATA")
    def identifier(self):
        self.protocol.get_reader_identifier()

    @analyze_data()
    def set_rf_power(
        self,
        antenna1=20,
        antenna2=20,
        antenna3=20,
        antenna4=20,
        antenna5=20,
        antenna6=20,
        antenna7=20,
        antenna8=20,
    ):
        logging.info("[SET RF POWER] Antenna1 = {}dBm".format(antenna1))
        logging.info("[SET RF POWER] Antenna2 = {}dBm".format(antenna2))
        logging.info("[SET RF POWER] Antenna3 = {}dBm".format(antenna3))
        logging.info("[SET RF POWER] Antenna4 = {}dBm".format(antenna4))
        logging.info("[SET RF POWER] Antenna5 = {}dBm".format(antenna5))
        logging.info("[SET RF POWER] Antenna6 = {}dBm".format(antenna6))
        logging.info("[SET RF POWER] Antenna7 = {}dBm".format(antenna7))
        logging.info("[SET RF POWER] Antenna8 = {}dBm".format(antenna8))
        self.protocol.set_rf_power(
            ant1=antenna1,
            ant2=antenna2,
            ant3=antenna3,
            ant4=antenna4,
            ant5=antenna5,
            ant6=antenna6,
            ant7=antenna7,
            ant8=antenna8,
        )

    @analyze_data("DATA")
    def get_rf_power(self):
        self.protocol.get_rf_power()

    @analyze_data()
    def fast_power(self, value=22):
        logging.info("[FAST SET RF POWER] {}dBm".format(value))
        self.protocol.fast_power(value=value)

    @analyze_data()
    def set_work_antenna(self, antenna=READER_ANTENNA["ANTENNA1"]):
        self.protocol.set_work_antenna(antenna=antenna)

    @analyze_data("DATA")
    def get_work_antenna(self):
        self.protocol.get_work_antenna()

    @analyze_data()
    def set_ant_connection_detector(self, loss=0):
        self.protocol.set_ant_connection_detector(loss=loss)

    @analyze_data("DATA")
    def get_ant_connection_detector(self):
        self.protocol.get_ant_connection_detector()

    def get_rf_port_return_loss(self, freq=FREQUENCY_TABLES[0]):
        try:
            param = FREQUENCY_TABLES.index(freq)
        except ValueError as err:
            logging.error(err)
            logging.error(FREQUENCY_TABLES)
            raise err

        self.protocol.get_rf_port_return_loss(param=param)
        value = ImpinjR2KReader.analyze_data("DATA")(lambda x, y: y)(self, None)
        if value[0] == 0xEE:
            logging.error("Get rf port return loss fail.")
            return 0
        return value[0]

    def rt_inventory(self, repeat=1):
        self.protocol.rt_inventory(repeat=repeat)

    def session_inventory(self, session="S1", target="A", repeat=1):
        self.protocol.session_inventory(session="S1", target="A", repeat=1)

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
            E=ImpinjR2KFastSwitchInventory.DISABLED,
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
        self.protocol.fast_switch_ant_inventory(param=param)

    @analyze_data()
    def beeper(self, mode=0):
        logging.info("BEEPER MODE : {}".format(mode))
        logging.info(
            """ MODE: \n 0 : Be quiet \n 1 : Sounds after each inventory \n 2 : Every time a tag is read """
        )
        self.protocol.beeper(mode=mode)

    def temperature(self):
        self.protocol.temperature()
        value = ImpinjR2KReader.analyze_data("DATA")(lambda x, y: y)(self, None)
        logging.info(
            "Reader temperature is {}C".format(value[1] * (-1 if value[0] == 0 else 1))
        )
        return value[1] * (-1 if value[0] == 0 else 1)

    def di(self, port):
        """Read GPIO
        @param -> port = 1 or 2
        """
        assert port in (1, 2)
        self.protocol.gpio(port=port)
        value = ImpinjR2KReader.analyze_data("DATA")(lambda x, y: y)(self, None)
        return value[0] if port == 1 else value[1]

    @analyze_data()
    def do(self, port, level=False):
        """Write GPIO
        @param -> port = 3 or 4
        """
        assert port in (3, 4)
        logging.info("SET GPIO-{} to {}".format(port, 1 if level else 0))
        self.protocol.gpio(port=port, level=level)

    # -------------------------------------------------
    def inventory(self, repeat=0xFF):
        self.protocol.inventory(repeat=repeat)
        value = ImpinjR2KReader.analyze_data("DATA")(lambda x, y: y)(self, None)
        if (value[0] == ImpinjR2KGlobalErrors.ANTENNA_MISSING_ERROR) or (
            value[0] == ImpinjR2KGlobalErrors.FAIL
        ):
            return 0

        try:
            antenna, tagcount, read_rate, read_total = struct.unpack(">BHHI", value)
        except BaseException as err:
            logging.error(err)
            logging.error("INVENTORY VALUE = {}".format(value))
            return 0

        logging.info("Antenna ID : {}".format(antenna + 1))
        logging.info("Tag count  : {}".format(tagcount))
        logging.info("Read rate  : {}/s".format(read_rate))
        logging.info("Read total : {}".format(read_total))
        return tagcount

    def get_inventory_buffer_tag_count(self):
        self.protocol.get_inventory_buffer_tag_count()
        value = ImpinjR2KReader.analyze_data("DATA")(lambda x, y: y)(self, None)
        if (value[0] == ImpinjR2KGlobalErrors.ANTENNA_MISSING_ERROR) or (
            value[0] == ImpinjR2KGlobalErrors.FAIL
        ):
            return 0
        count = struct.unpack(">H", value)[0]
        logging.info("Inventory buffer tag count {}".format(count))
        return count

    def __unpack_inventory_buffer(self, data):
        try:
            count, length = struct.unpack(">HB", data[0:3])
        except BaseException as err:
            logging.error(err)
            return ""

        if (length + 6) != len(data):
            return ""

        pc = struct.unpack(">H", data[3:5])[0]
        size = ((pc & 0xF800) >> 10) & 0x003E
        epc = "".join(["%02X" % x for x in data[5 : size + 5]])

        crc = struct.unpack(">H", data[size + 5 : size + 5 + 2])[0]
        if crc != (libscrc.xmodem(data[3 : size + 5], 0xFFFF) ^ 0xFFFF):
            logging.error("TAGS CRC16 is ERROR.")
            return ""

        rssi = data[-3] - 129
        ant = (data[-2] & 0x03) + 1  # Bugfix:20200303

        # When high bit is 0: Antenna ID 1/2/3/4;
        # When high bit is 1: Antenna ID 5/6/7/8.
        # Note：The High bit just used to get Ant ID, no RSSI.
        if rssi > 0:
            ant += 4
            rssi -= 128

        invcount = data[-1]

        logging.debug("*" * 50)
        logging.debug("COUNT    : {}".format(count))
        logging.debug("EPC      : {}".format(epc))
        logging.debug("CRC      : {:X}".format(crc))
        logging.debug("RSSI     : {}".format(rssi))
        logging.debug("ANT      : {}".format(ant))
        logging.debug("INVCOUNT : {}".format(invcount))

        return (ant, rssi, epc)

    def get_inventory_buffer(self, loop=1):
        """
        @return : ( ant, rssi, epc ) -> tuple
        """
        tags = []
        self.protocol.get_inventory_buffer()
        for _ in range(loop):
            value = ImpinjR2KReader.analyze_data("DATA")(lambda x, y: y)(self, None)
            tags.append(self.__unpack_inventory_buffer(value))
        return tags

    def get_and_reset_inventory_buffer(self, loop=1):
        """
        @return : ( ant, rssi, epc ) -> tuple
        """
        tags = []
        self.protocol.get_and_reset_inventory_buffer()
        for _ in range(loop):
            value = ImpinjR2KReader.analyze_data("DATA")(lambda x, y: y)(self, None)
            tags.append(self.__unpack_inventory_buffer(value))
        ### Bugfix:20200302
        value = ImpinjR2KReader.analyze_data("DATA")(lambda x, y: y)(self, None)
        logging.info(
            "GET_AND_RESET_INVENTORY_BUFFER = {}".format(
                ImpinjR2KGlobalErrors.to_string(value[0])
            )
        )
        return tags

    @analyze_data()
    def reset_inventory_buffer(self):
        self.protocol.reset_inventory_buffer()

    # # # -------------------------------------------------
    @analyze_data(timeout=5)
    def set_access_epc_match(self, mode=0, epc="00" * 12):
        self.protocol.set_access_epc_match(mode=mode, epc=list(bytearray.fromhex(epc)))

    def read(self, epc: str, bank="EPC", address=0, size=2, password=[0] * 4):
        """
        EPC  -> address=0, size=8
        TID  -> address=0, size=3
        USER -> address=0, size=2
        """
        result = self.set_access_epc_match(mode=0, epc=epc)
        if (len(result) == 0) or (not result[0]):
            return ""

        self.protocol.read(bank=bank, addr=address, size=size, password=password)
        value = ImpinjR2KReader.analyze_data("DATA", timeout=5)(lambda x, y: y)(
            self, None
        )

        try:
            count, length = struct.unpack(">HB", value[0:3])
        except BaseException:
            logging.error(ImpinjR2KGlobalErrors.to_string(value[0]))
            return ""

        pc = struct.unpack(">H", value[3:5])[0]
        size = ((pc & 0xF800) >> 10) & 0x003E
        epc = "".join(["%02X" % x for x in value[5 : size + 5]])

        crc = struct.unpack(">H", value[size + 5 : size + 5 + 2])[0]
        if crc != (libscrc.xmodem(value[3 : size + 5], 0xFFFF) ^ 0xFFFF):
            logging.error("TAGS CRC16 IS ERROR.")
            return ""

        datasize = value[-3]
        antenna = (value[-2] & 0x03) + 1
        invcount = value[-1]

        data_offset_head = size + 5 + 2
        data_offset_tail = data_offset_head + datasize

        data = "".join(["%02X" % x for x in value[data_offset_head:data_offset_tail]])

        logging.debug("*" * 50)
        logging.debug("COUNT    : {}".format(count))
        logging.debug("LENGTH   : {}".format(length))
        logging.debug("SIZE     : {}".format(size))
        logging.debug("EPC      : {}".format(epc))
        logging.debug("CRC      : {:X}".format(crc))
        logging.debug("DATA     : {}".format(data))
        logging.debug("DATASIZE : {}".format(datasize))
        logging.debug("ANT      : {}".format(antenna))
        logging.debug("INVCOUNT : {}".format(invcount))

        return data

    def write(self, epc: str, data: str, bank="EPC", address=0, password=[0] * 4):
        """Write Tag to ( EPC, TID, USER )
        EPC  -> address=2, size=8
        TID  -> address=0, size=3
        USER -> address=0, size=2
        """
        assert (type(epc) is str) and (type(data) is str)

        result = self.set_access_epc_match(mode=0, epc=epc)
        if (len(result) == 0) or (not result[0]):
            return ""

        try:
            self.protocol.write_block(
                list(bytearray.fromhex(data)),
                bank=bank,
                addr=address,
                password=password,
            )
        except BaseException:
            logging.error("Data must be hex string.")
            return ""

        value = ImpinjR2KReader.analyze_data("DATA")(lambda x, y: y)(self, None)

        try:
            count, length = struct.unpack(">HB", value[0:3])
        except BaseException:
            logging.error(ImpinjR2KGlobalErrors.to_string(value[0]))
            return ""

        if (length + 6) != len(value):
            return ""

        pc = struct.unpack(">H", value[3:5])[0]
        size = ((pc & 0xF800) >> 10) & 0x003E
        epc = "".join(["%02X" % x for x in value[5 : size + 5]])

        crc = struct.unpack(">H", value[size + 5 : size + 5 + 2])[0]
        if crc != (libscrc.xmodem(value[3 : size + 5], 0xFFFF) ^ 0xFFFF):
            logging.error("TAGS CRC16 is ERROR.")
            return ""

        error = (
            True if value[-3] == ImpinjR2KGlobalErrors.SUCCESS else False,
            ImpinjR2KGlobalErrors.to_string(value[-3]),
        )
        ant = (value[-2] & 0x03) + 1
        wcount = value[-1]

        logging.debug("*" * 50)
        logging.debug("COUNT      : {}".format(count))
        logging.debug("EPC        : {}".format(epc))
        logging.debug("CRC        : {:X}".format(crc))
        logging.debug("ERROR      : {}".format(error))
        logging.debug("ANT        : {}".format(ant))
        logging.debug("WriteCount : {}".format(wcount))

        return epc

    # # # -------------------------------------------------
    @analyze_data()
    def set_frequency_region_user(self, start_khz, space_khz, quantity):
        self.protocol.set_frequency_region_user(
            start=start_khz, space=space_khz, quantity=quantity
        )

    @analyze_data()
    def set_frequency_region(self, start, stop, region=ImpinjR2KRegion.FCC):
        """ """
        assert FREQUENCY_TABLES[0] <= stop <= FREQUENCY_TABLES[-1], (
            "SEE: constant.FREQUENCY_TABLES"
        )
        assert FREQUENCY_TABLES[0] <= start <= FREQUENCY_TABLES[-1], (
            "SEE: constant.FREQUENCY_TABLES"
        )
        assert start <= stop

        try:
            start = FREQUENCY_TABLES.index(start)
            stop = FREQUENCY_TABLES.index(stop)
        except ValueError as err:
            logging.error(err)
            logging.error(FREQUENCY_TABLES)
            raise err

        self.protocol.set_frequency_region(region=region, start=start, stop=stop)

    def get_frequency_region(self):
        self.protocol.get_frequency_region()
        value = ImpinjR2KReader.analyze_data("DATA")(lambda x, y: y)(self, None)

        REGION = {0: "ERROR", 1: "FCC", 2: "ETSI", 3: "CHN", 4: "USER"}

        logging.debug("Region : {}".format(REGION.get(value[0], "ERRROR")))
        if value[0] != ImpinjR2KRegion.USER:
            return dict(
                Region=REGION.get(value[0], "ERRROR"),
                StartFreq=FREQUENCY_TABLES[value[1]],
                EndFreq=FREQUENCY_TABLES[value[2]],
            )

        StartFreq = (
            ((value[3] << 16) & 0x00FF0000) + ((value[4] << 8) & 0x0000FF00) + value[5]
        )
        return dict(
            Region=REGION.get(value[0], "ERRROR"),
            FreqSpace=value[1] // 10,
            Quantity=value[2],
            StartFreq=StartFreq,
        )

    # # # -------------------------------------------------
    # # # Other functions.
    def distance(self, rssi, A=60, n=3.5):
        """
        @Param
            rssi : Signal strength
            A : Signal strength at a distance of 1m between the transmitter and the receiver
            n : Environmental factor ( 2 - 5)
        """
        return 10 ** ((abs(rssi) - A) / (10 * n))

    def get_average(self, data: list):
        return sum(data) / len(data)

    def get_variance(self, data: list):
        average = get_average(data)
        return sum([(x - average) ** 2 for x in data]) / len(data)
