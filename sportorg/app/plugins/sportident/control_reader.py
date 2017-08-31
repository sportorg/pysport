import threading
import time
import serial
from sportorg.lib.sportident import sireader


class SIControlThread(threading.Thread):
    def __init__(self, port, func=lambda card_data: card_data):
        super().__init__()
        self.port = port
        self.readers = [func]
        self.cards = []
        self._reading = True

    @property
    def reading(self):
        return self._reading

    def add_card_data(self, card_data):
        for f in self.readers:
            f(card_data)
        self.cards.append(card_data)

    def run(self):
        si = sireader.SIReaderControl(port=self.port, debug=True)
        while True:
            try:
                punches = si.poll_punch()
                while not punches:
                    time.sleep(0.5)
                    if not self.reading:
                        si.disconnect()
                        return
                    punches = si.poll_punch()
                print(punches)


            except sireader.SIReaderException as e:
                print(str(e))
            except sireader.SIReaderCardChanged as e:
                print(str(e))
            except serial.serialutil.SerialException:
                self.stop()
                return

    def stop(self):
        self._reading = False

    def append_reader(self, f):
        self.readers.append(f)

        return len(self.readers)

    def delete_reader(self, func_id):
        del self.readers[func_id-1]


def get_ports():
    ports = []
    for i in range(32):
        try:
            p = 'COM' + str(i)
            com = serial.Serial(p, 38400, timeout=5)
            com.close()
            ports.append(p)
        except serial.SerialException:
            continue

    return ports


def choose_port():
    ports = get_ports()
    if len(ports):
        print("Доступные порты:")
        for i, p in enumerate(ports):
            print("{} - {}".format(i, p))

        return ports[0]
    else:
        print("Нет доступных портов")
        return None


if __name__ == '__main__':
    port = choose_port()
    if port is not None:
        reader = SIControlThread(port)
        reader.start()
