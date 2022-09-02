import struct

import pytest

from sportorg.libs.winorient.wdb import (
    WDB,
    WDBChip,
    WDBDistance,
    WDBFinish,
    WDBGroup,
    WDBMan,
    WDBPunch,
    WDBTeam,
    parse_wdb,
)


def test_WDBPunch_parsing():
    # 31 code
    # 10:00:00 = 10*3600*100 = 3600000
    code = 31
    time = 3600000

    byte_array = struct.pack('<I', code) + struct.pack('<I', time)
    obj1 = WDBPunch()
    obj1.parse_bytes(byte_array)
    obj2 = WDBPunch(code, time)

    assert obj1.code == obj2.code
    assert obj1.time == obj2.time
    assert byte_array == obj2.get_bytes()


def test_WDBFinish_parsing():
    # 1023 number
    # 10:00:00 = 10*3600*100 = 3600000
    # 101 sound
    number = 1023
    time = 3600000
    sound = 101

    byte_array = (
        struct.pack('<I', number) + struct.pack('<I', time) + struct.pack('<I', sound)
    )
    obj1 = WDBFinish()
    obj1.parse_bytes(byte_array)
    obj2 = WDBFinish()
    obj2.create(number, time, sound)

    assert obj1.number == obj2.number
    assert obj1.time == obj2.time
    assert obj1.sound == obj2.sound
    assert byte_array == obj2.get_bytes()


def test_WDBChip_parsing():
    obj1 = WDBChip()
    obj1.id = 1600888
    obj1.quantity = 2
    obj1.punch.append(WDBPunch(31, 450000))
    obj1.punch.append(WDBPunch(32, 453000))

    byte_array = obj1.get_bytes()
    obj2 = WDBChip()
    obj2.parse_bytes(byte_array)
    assert obj1.id == obj2.id


def test_WDBTeam_parsing():
    obj1 = WDBTeam()
    obj1.id = 766
    obj1.name = 'Команда 6673'

    byte_array = obj1.get_bytes()
    obj2 = WDBTeam()
    obj2.parse_bytes(byte_array)
    assert obj1.name == obj2.name
    assert len(byte_array) == 56


def test_WDBDistance_parsing():
    obj1 = WDBDistance()
    obj1.id = 766
    obj1.name = 'Длинн 2'
    obj1.penalty_seconds = 19

    byte_array = obj1.get_bytes()
    obj2 = WDBDistance()
    obj2.parse_bytes(byte_array)
    assert obj1.name == obj2.name
    assert obj1.penalty_seconds == obj2.penalty_seconds
    assert len(byte_array) == 352


def test_WDBGroup_parsing():
    obj1 = WDBGroup()
    obj1.id = 766
    obj1.name = 'Длинн2'
    obj1.owner_discount_cost = 1200
    obj1.distance_id = 120

    byte_array = obj1.get_bytes()
    obj2 = WDBGroup()
    obj2.parse_bytes(byte_array)
    assert obj1.name == obj2.name
    assert obj1.distance_id == obj2.distance_id
    assert obj1.owner_discount_cost == obj2.owner_discount_cost
    assert len(byte_array) == 36


def test_WDBMan_parsing():
    obj1 = WDBMan(WDB())
    obj1.name = 'Ахтаров Данил'
    obj1.round = 4
    obj1.is_finished = True

    byte_array = obj1.get_bytes()
    obj2 = WDBMan(WDB())
    obj2.parse_bytes(byte_array)
    assert obj1.name == obj2.name
    assert obj1.finished == obj2.finished
    assert len(byte_array) == 196


@pytest.mark.skip(reason='Not working')
def test_WDB_read_file():
    file_path = 'tests/data/test.wdb'
    wdb_object = parse_wdb(file_path)

    file_path_out = 'data/test.wdb'
    wdb_file_out = open(file_path_out, 'wb')
    test_out = wdb_object.get_bytes()
    wdb_file_out.write(test_out)
    wdb_file_out.close()
    byte_array_in = open(file_path, 'rb').read()
    byte_array_out = open(file_path_out, 'rb').read()

    assert byte_array_in == byte_array_out
