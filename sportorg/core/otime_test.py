import unittest
from sportorg.core.otime import *


class TestStringMethods(unittest.TestCase):
    def test_otime(self):
        vals = [
            ((1, 13, 5, 35), (1, 13, 5, 35), '37:05:35'),
            ((1, 13, 15, 35), (1, 13, 15, 35), '37:15:35'),
            ((2, 26, 5, 35), (3, 2, 5, 35), '74:05:35'),
            ((0, 26, 5, 35), (1, 2, 5, 35), '26:05:35'),
            ((0, 0, 5, 35), (0, 0, 5, 35), '0:05:35'),
            ((0, 185, 0, 0), (7, 17, 0, 0), '185:00:00'),
        ]
        for i in range(len(vals)):
            time = OTime(*vals[i][0])
            self.assertEqual(vals[i][1][0], time.day, 'Day error, #iter-' + str(i))
            self.assertEqual(vals[i][1][1], time.hour, 'Hour error, #iter-' + str(i))
            self.assertEqual(vals[i][1][2], time.minute, 'Minute error, #iter-' + str(i))
            self.assertEqual(vals[i][1][3], time.sec, 'Second error, #iter-' + str(i))
            self.assertEqual(vals[i][2], str(time), 'Str error, #iter-' + str(i))

    def test_otime_eq(self):
        otime1 = OTime(0, 0, 25, 44)
        otime2 = OTime(0, 0, 25, 44)
        self.assertEqual(True, otime1 == otime2, 'Error')


if __name__ == '__main__':
    unittest.main()
