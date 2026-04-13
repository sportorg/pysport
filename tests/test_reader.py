import os
import platform
import time
import subprocess
import serial
from threading import Thread, Event
from sportorg.models.memory import race
from PySide2.QtCore import QObject, Slot, Signal, QCoreApplication, QTimer
import pytest

from sportorg.modules.sportiduino.sportiduino import SportiduinoClient
from sportorg.modules.sportident.sireader import SIReaderClient
from sportorg.modules.huichang.huichang import HuichangClient


class SportiduinoEmulator(Thread):
    KNOWN_MSGS = {
        b'\xfe\x46\x00\x46': [b'\xfe\x66\x03\x01\x09\x00\x73'],
        b'\xfe\x4b\x00\x4b': [
            b'\xfe\x63\x1e\x01\x90\x00\x00\x00\x00\x00\x00\x00\x00\xf0\x67\x2f\xaf\xe0\x25\x67\x2f\xb4\xcf\x26\x67\x2f\xbc\x92\x23\x67\x2f\x28',
            b'\xfe\x63\x1f\xbf\x63\x24\x67\x2f\xc1\x24\x34\x67\x2f\xc4\x5d\x31\x67\x2f\xc6\x90\x30\x67\x2f\xc9\x27\x22\x67\x2f\xd0\xb0\x21\x5a',
            b'\xfe\x63\x18\x67\x2f\xd7\x09\x20\x67\x2f\xdd\xb1\x1f\x67\x2f\xdf\x28\x35\x67\x2f\xe5\x63\xf5\x67\x2f\xe7\xd9\x4f',
        ],
    }

    def __init__(self, link, stop_event):
        super().__init__()
        self.link = link
        self.stop_event = stop_event
        self.daemon = True
        self.start()

    def run(self):
        ser = serial.Serial(self.link, baudrate=38400, timeout=1)
        print(f"Emulating sportiduino on {self.link}...")
        repled = set()
        while not self.stop_event.is_set():
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                #print('<='+' '.join(format(x, '02x') for x in data))

                if data in self.KNOWN_MSGS and data not in repled:
                    for msg in self.KNOWN_MSGS[data]:
                        ser.write(msg)
                        #print('=>'+' '.join(format(x, '02x') for x in msg))
                        time.sleep(0.01)
                    repled.add(data)
        ser.close()


class SPORTidentEmulator(Thread):
    KNOWN_MSGS = {
        b'\x02\xf0\x01\x4d\x6d\x0a\x03': [b'\x02\xf0\x03\x00\x09\x4d\x8d\x22\x03'],
        b'\x02\x83\x02\x74\x01\x04\x14\x03': [b'\x02\x83\x04\x00\x09\x74\x05\x31\xc7\x03'],
        b'\x02\x83\x02\x71\x01\x1a\x14\x03': [
            b'\x02\x83\x04\x00\x09\x71\x05\x2f\xc7\x03',
            b'\x02\xe8\x06\x00\x09\x0f\x84\x14\xd8\xbb\x0f\x03',
        ],
        b'\x02\xef\x01\x00\xe2\x09\x03': [
            b'\x02\xef\x83\x00\x09\x00\x00\xf4\x4b\x9d\xea\xea\xea\xea\x0d\x02\x0a\x26\x1d\x02\x0a\x36'
            b'\x8d\xf1\x19\xd1\x0e\x62\x0f\x7f\x0f\x84\x14\xd8\x0c\x11\xbb\xd6\x38\x36\x35\x36\x30\x38'
            b'\x38\x3b\x3b\x3b\x3b\x3b\x3b\x3b\x67\x2e\x20\x4d\x6f\x73\x6b\x61\x75\x3b\x75\x6c\x2e\x20'
            b'\x41\x6b\x61\x64\x65\x6d\x69\x6b\x61\x20\x42\x61\x6b\x75\x6c\x65\x76\x61\x2c\x20\x64\x2e'
            b'\x38\x2c\x20\x6b\x76\x2e\x35\x34\x3b\x31\x31\x37\x35\x31\x33\x3b\x52\x55\x53\x3b\x00\x00'
            b'\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee'
            b'\xee\xee\xbb\xa6\x03'
        ],
        b'\x02\xef\x01\x04\xe6\x09\x03': [
            b'\x02\xef\x83\x00\x09\x04\x0d\x23\x0b\x57\x0d\x23\x0b\x6a\x0d\x57\x0c\xa9\x0d\x21\x0d\x80'
            b'\x0d\x36\x0f\xdc\x0d\x25\x11\x50\x0d\x2e\x11\xff\x0d\x3d\x12\xa3\x0d\x5e\x13\x9f\x0d\x47'
            b'\x14\xa2\x0d\x35\x15\xa8\x0d\x2b\x16\x5d\x0d\x4c\x16\xd5\x0d\x26\x18\x22\x0d\x24\x18\xf4'
            b'\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee'
            b'\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee'
            b'\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee\xee'
            b'\xee\xee\x76\x6f\x03'
        ]
    }

    def __init__(self, link, stop_event):
        super().__init__()
        self.link = link
        self.stop_event = stop_event
        self.daemon = True
        self.start()

    def run(self):
        ser = serial.Serial(self.link, baudrate=38400, timeout=1)
        print(f"Emulating SPORTident on {self.link}...")
        repled = set()
        while not self.stop_event.is_set():
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                #print('<='+' '.join(format(x, '02x') for x in data))

                if data[:2] == b'\xff\x02':
                    data = data[2:]

                if data in self.KNOWN_MSGS and data not in repled:
                    for msg in self.KNOWN_MSGS[data]:
                        ser.write(msg)
                        #print('=>'+' '.join(format(x, '02x') for x in msg))
                        time.sleep(0.01)
                    repled.add(data)
        ser.close()


class HuichangEmulator(Thread):
    CARD_DATA = [
        [
            b'\xaa\xbb\xff\x20\x13\x61\x01\x30\x26\xff\xff\xff\xff\xff\x15\x12\x27\x05\x04\x06\x12\x26\x2e\x26',
            b'\xaa\xbb\xff\x20\x0d\x21\x12\x26\x38\x21\x12\x27\x01\x21\x12\x27\x07\x2f',
            b'\xaa\xbb\xff\x20\x01\xff',
            b'\xaa\xbb\xff\xa1\x02\x1d\x39'
        ],
        [
            b'\xaa\xbb\xff\x60\x13\x33\x07\x89\x90\x0b\x05\x1a\x37\x02\x15\x35\x1b\x00\x03\x06\x05\x1a\x36\x64',
            b'\xaa\xbb\xff\x60\x15\x1f\x05\x1a\x37\x20\x05\x1a\x3a\x21\x05\x1a\x3b\x22\x05\x1a\x3b\x23\x05\x1a\x3b\xfd',
            b'\xaa\xbb\xff\x60\x01\xff'
        ],
    ]

    def __init__(self, link, stop_event):
        super().__init__()
        self.link = link
        self.stop_event = stop_event
        self.daemon = True
        self.start()

    def run(self):
        ser = serial.Serial(self.link, baudrate=9600, timeout=1)
        print(f"Emulating Huichang on {self.link}...")
        connected = False
        while not self.stop_event.is_set():
            if connected:
                time.sleep(1)
                for packets in self.CARD_DATA:
                    for p in packets:
                        ser.write(p)
                        time.sleep(0.01)
                    time.sleep(0.5)
                connected = False
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                print('<='+' '.join(format(x, '02x') for x in data))

                if data[:3] == b'\xaa\xbb\xff':
                    if data[3] == 0x28:
                        print("Switching Huichang master station to Online/Offline mode")
                        connected = True
                    # Send Ok
                    msg = b"\xaa\xbb\xff" + bytes([data[3]]) + b"\x02\xcc\x6d"
                    ser.write(msg)
                    #print('=>'+' '.join(format(x, '02x') for x in msg))
                    time.sleep(0.01)
        ser.close()


def start_socat():
    link1 = '/tmp/pty0'
    link2 = '/tmp/pty1'
    socat_command = f'socat pty,raw,echo=0,link={link1} pty,raw,echo=0,link={link2}'
    print(f"Starting socat process: {socat_command}")
    process = subprocess.Popen(socat_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    time.sleep(1)  # Allow time for the PTYs to be created
    return process, link1, link2

def stop_socat(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        print("Socat process terminated.")


class ResultHandler(QObject):
    def __init__(self):
        super().__init__()
        self.results = []

    @Slot(object)
    def add_result_from_reader(self, result):
        self.results.append(result)

@pytest.fixture
def socat():
    socat_process, link1, link2 = start_socat()
    yield socat_process, link1, link2
    stop_socat(socat_process)

@pytest.fixture
def result_handler():
    return ResultHandler()

@pytest.fixture
def app():
    app = QCoreApplication.instance() or QCoreApplication([])  # For event loop
    yield app
    app.quit()

@pytest.fixture
def set_utc_timezone():
    # Save the current TZ environment variable to restore it later
    original_tz = os.environ.get("TZ")

    # Set the desired timezone to UTC
    os.environ["TZ"] = "UTC"

    # Apply the change
    time.tzset()

    yield

    # Restore the original timezone
    if original_tz is not None:
        os.environ["TZ"] = original_tz
    else:
        del os.environ["TZ"]

    # Reapply the original timezone
    time.tzset()

@pytest.mark.skipif(platform.system() != 'Linux', reason="This test only works on Linux")
def test_sportiduino(app, result_handler, socat, set_utc_timezone):
    _, link1, link2 = socat

    stop_event = Event()
    emulator_thread = SportiduinoEmulator(link1, stop_event)

    race().set_setting('system_port', link2)

    SportiduinoClient().set_call(result_handler.add_result_from_reader)
    SportiduinoClient().start()

    # Run the event loop for a few seconds to allow the signal to be processed
    QTimer.singleShot(5000, app.quit)
    app.exec_()

    SportiduinoClient().stop()
    stop_event.set()
    #emulator_thread.quit()
    emulator_thread.join()

    assert len(result_handler.results) == 1
    result = result_handler.results[0]
    assert result.card_number == 400
    assert str(result.start_time) == '18:54:24'
    assert str(result.finish_time) == '22:53:13'

    expected = [
        (37, '19:15:27'),
        (38, '19:48:34'),
        (35, '20:00:35'),
        (36, '20:08:04'),
        (52, '20:21:49'),
        (49, '20:31:12'),
        (48, '20:42:15'),
        (34, '21:14:24'),
        (33, '21:41:29'),
        (32, '22:09:53'),
        (31, '22:16:08'),
        (53, '22:42:43'),
    ]

    for i, split in enumerate(result.splits):
        assert (int(split.code), str(split.time)) == expected[i]

@pytest.mark.skipif(platform.system() != 'Linux', reason="This test only works on Linux")
def test_sportident(app, result_handler, socat):
    _, link1, link2 = socat

    stop_event = Event()
    emulator_thread = SPORTidentEmulator(link1, stop_event)

    race().set_setting('system_port', link2)

    SIReaderClient().set_call(result_handler.add_result_from_reader)
    SIReaderClient().start()

    # Run the event loop for a few seconds to allow the signal to be processed
    QTimer.singleShot(5000, app.quit)
    app.exec_()

    SIReaderClient().stop()
    stop_event.set()
    emulator_thread.join()

    assert len(result_handler.results) == 1
    result = result_handler.results[0]
    assert result.card_number == 8656088
    assert str(result.start_time) == '12:43:34'
    assert str(result.finish_time) == '13:50:09'

    expected = [
        (35, '12:48:23'),
        (35, '12:48:42'),
        (87, '12:54:01'),
        (33, '12:57:36'),
        (54, '13:07:40'),
        (37, '13:13:52'),
        (46, '13:16:47'),
        (61, '13:19:31'),
        (94, '13:23:43'),
        (71, '13:28:02'),
        (53, '13:32:24'),
        (43, '13:35:25'),
        (76, '13:37:25'),
        (38, '13:42:58'),
        (36, '13:46:28'),
    ]

    for i, split in enumerate(result.splits):
        assert (int(split.code), str(split.time)) == expected[i]


@pytest.mark.skipif(platform.system() != 'Linux', reason="This test only works on Linux")
def test_huichang(app, result_handler, socat):
    _, link1, link2 = socat

    stop_event = Event()
    emulator_thread = HuichangEmulator(link1, stop_event)

    race().set_setting('system_port', link2)
    #race().set_setting('time_accuracy', 2)

    HuichangClient().set_call(result_handler.add_result_from_reader)
    HuichangClient().start()

    # Run the event loop for a few seconds to allow the signal to be processed
    QTimer.singleShot(5000, app.quit)
    app.exec_()

    HuichangClient().stop()
    stop_event.set()
    emulator_thread.join()

    assert len(result_handler.results) == 2

    result = result_handler.results[0]
    assert result.card_number == 61013026
    assert str(result.start_time) == '00:00:00'
    assert str(result.finish_time) == '18:39:05'
    assert result.card_battery_level == 29
    # clear = 18:38:46
    expected = [
        (33, '18:38:56'),
        (33, '18:39:01'),
        (33, '18:39:07'),
    ]
    for i, split in enumerate(result.splits):
        assert (int(split.code), str(split.time)) == expected[i]

    result = result_handler.results[1]
    assert result.card_number == 33078990
    assert str(result.start_time) == '05:26:55'
    assert str(result.finish_time) == '05:27:00'
    # clear = 05:26:54
    expected = [
        (31, '05:26:55'),
        (32, '05:26:58'),
        (33, '05:26:59'),
        (34, '05:26:59'),
        (35, '05:26:59'),
    ]
    for i, split in enumerate(result.splits):
        assert (int(split.code), str(split.time)) == expected[i]

