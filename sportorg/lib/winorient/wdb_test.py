import struct
import unittest

from sportorg.app.plugins.winorient.wdb import WinOrientBinary
from sportorg.lib.winorient.wdb import WDBPunch, WDBFinish, WDBChip, WDBTeam, WDBDistance, WDBGroup, WDBMan, \
    parse_wdb, WDB


class TestStringMethods(unittest.TestCase):

    def test_WDBPunch_parsing(self):
        # 31 code
        # 10:00:00 = 10*3600*100 = 3600000
        code = 31
        time = 3600000

        byte_array = struct.pack("<I", code) + struct.pack("<I", time)
        obj1 = WDBPunch()
        obj1.parse_bytes(byte_array)
        obj2 = WDBPunch(code, time)

        self.assertEqual(obj1.code, obj2.code)
        self.assertEqual(obj1.time, obj2.time)
        self.assertEqual(byte_array, obj2.get_bytes())

    def test_WDBFinish_parsing(self):
        # 1023 number
        # 10:00:00 = 10*3600*100 = 3600000
        # 101 sound
        number = 1023
        time = 3600000
        sound = 101

        byte_array = struct.pack("<I", number) + struct.pack("<I", time) + struct.pack("<I", sound)
        obj1 = WDBFinish()
        obj1.parse_bytes(byte_array)
        obj2 = WDBFinish()
        obj2.create(number, time, sound)

        self.assertEqual(obj1.number, obj2.number)
        self.assertEqual(obj1.time, obj2.time)
        self.assertEqual(obj1.sound, obj2.sound)
        self.assertEqual(byte_array, obj2.get_bytes())

    def test_WDBChip_parsing(self):
        obj1 = WDBChip()
        obj1.id = 1600888
        obj1.quantity = 2
        obj1.punch.append(WDBPunch(31, 450000))
        obj1.punch.append(WDBPunch(32, 453000))

        byte_array = obj1.get_bytes()
        obj2 = WDBChip()
        obj2.parse_bytes(byte_array)
        self.assertEqual(obj1.id, obj2.id)

    def test_WDBTeam_parsing(self):
        obj1 = WDBTeam()
        obj1.id = 766
        obj1.name = 'Команда 6673'

        byte_array = obj1.get_bytes()
        obj2 = WDBTeam()
        obj2.parse_bytes(byte_array)
        self.assertEqual(obj1.name, obj2.name)
        self.assertEqual(len(byte_array), 56)

    def test_WDBDistance_parsing(self):
        obj1 = WDBDistance()
        obj1.id = 766
        obj1.name = 'Длинн 2'
        obj1.penalty_seconds = 19

        byte_array = obj1.get_bytes()
        obj2 = WDBDistance()
        obj2.parse_bytes(byte_array)
        self.assertEqual(obj1.name, obj2.name)
        self.assertEqual(obj1.penalty_seconds, obj2.penalty_seconds)
        self.assertEqual(len(byte_array), 352)

    def test_WDBGroup_parsing(self):
        obj1 = WDBGroup()
        obj1.id = 766
        obj1.name = 'Длинн2'
        obj1.owner_discount_cost = 1200
        obj1.distance_id = 120

        byte_array = obj1.get_bytes()
        obj2 = WDBGroup()
        obj2.parse_bytes(byte_array)
        self.assertEqual(obj1.name, obj2.name)
        self.assertEqual(obj1.distance_id, obj2.distance_id)
        self.assertEqual(obj1.owner_discount_cost, obj2.owner_discount_cost)
        self.assertEqual(len(byte_array), 36)

    def test_WDBMan_parsing(self):
        obj1 = WDBMan(WDB())
        obj1.name = 'Ахтаров Данил'
        obj1.round = 4
        obj1.is_finished = True

        byte_array = obj1.get_bytes()
        obj2 = WDBMan(WDB())
        obj2.parse_bytes(byte_array)
        self.assertEqual(obj1.name, obj2.name)
        self.assertEqual(obj1.round, obj2.round)
        self.assertEqual(obj1.finished, obj2.finished)
        self.assertEqual(len(byte_array), 196)

    def test_WDB_read_file(self):
        file_path = 'C:\\tmp\\test.wdb'
        wdb_object = parse_wdb(file_path)

        file_path_out = file_path.replace('.wdb', '_out.wdb')
        wdb_file_out = open(file_path_out, 'wb')
        test_out = wdb_object.get_bytes()
        wdb_file_out.write(test_out)
        wdb_file_out.close()
        byte_array_in = open(file_path, 'rb').read()
        byte_array_out = open(file_path_out, 'rb').read()

        self.assertEqual(byte_array_in, byte_array_out)

    def test_import_export(self):
        file_path = 'C:\\tmp\\test.wdb'
        wdb_object = parse_wdb(file_path)
        WinOrientBinary().create_objects()
        wdb_object2 = WinOrientBinary().export()
        test1 = wdb_object.get_bytes()
        test2 = wdb_object2.get_bytes()

        self.assertEqual(test1, test2)