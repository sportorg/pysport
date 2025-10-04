import logging
import struct
from enum import Enum


class ObjectTypes(Enum):
    """
    ```python
    obj_type = ObjectTypes['Race']
    obj_type.value
    ```
    """

    Race = 0
    Course = 1
    Group = 2
    Organization = 3
    Person = 4
    Result = 5
    ResultManual = 6
    ResultSportident = 7
    ResultSFR = 8
    ResultSportiduino = 9
    ResultRfidImpinj = 10
    ResultSrpid = 11
    ResultRuident = 12
    Unknown = 255

    def __str__(self):
        return self._name_

    def __repr__(self):
        return self.__str__()


class Operations(Enum):
    """
    ```python
    op = Operations['Create']

    Operations(0).name
    'Create'
    ```
    """

    Create = 0
    Read = 1
    Update = 2
    Delete = 3
    SyncRace = 4
    GetLock = 5
    ReleaseLoc = 6

    def __str__(self):
        return self._name_

    def __repr__(self):
        return self.__str__()


class Header:
    """
    ```
    ?: boolean
    H: Unsigned short
    L: unsigned long
    i: int
    f: float
    Q: Unsigned long long int
    s: bytes string

    Header Tag: 2 Bytes
    Operation type:  1 Byte (Unsigned Short)
    Object type: 1 Byte (Unsigned Short)
    uuid: 36 Bytes string
    version: 4 Bytes (Unsigned Long)
    size: 8 Bytes (Unsigned Long long)

    Total Header Size = 56 Bytes
    ```
    """

    header_struck = "=2s2H36sLQ"
    header_size = struct.calcsize(header_struck)

    def __init__(self, obj_data=None, op_type=Operations.Update.name):
        self.pack_tag = b"SO"
        if obj_data:
            try:
                obj_type = obj_data["object"]
                # obj_ver = obj_data['version']
                obj_uuid = obj_data["id"]
            except AttributeError:
                raise ValueError
            logging.debug(
                "Header Init: obj_type: {}, op_type: {}, uuid: {}".format(
                    obj_type, op_type, obj_uuid
                )
            )
            self.op_type = Operations[op_type].value
            self.obj_type = ObjectTypes[obj_type].value
            self.uuid = obj_uuid
            self.version = 0  # int(obj_ver)
            self.size = len(obj_data)
        else:
            self.op_type = Operations[op_type].value
            self.obj_type = 0
            self.uuid = ""
            self.version = 0  # int(obj_ver)
            self.size = 0

    def unpack_header(self, header):
        (
            self.pack_tag,
            self.op_type,
            self.obj_type,
            self.uuid,
            self.version,
            self.size,
        ) = struct.unpack(Header.header_struck, header)

    def prepare_header(self, obj_data, op_type):
        try:
            obj_type = obj_data["object"]
            # obj_ver = obj_data['version']
            obj_uuid = obj_data["id"]
        except AttributeError:
            return False
        self.op_type = Operations[op_type].value

        try:
            self.obj_type = ObjectTypes[obj_type].value
        except Exception:
            self.obj_type = 255  # Unknown

        self.uuid = obj_uuid
        self.version = 0  # int(obj_ver)
        self.size = len(obj_data)
        return True

    def pack_header(self, psize):
        self.size = psize
        return struct.pack(
            Header.header_struck,
            self.pack_tag,
            self.op_type,
            self.obj_type,
            bytes(self.uuid, "ascii"),
            self.version,
            self.size,
        )
