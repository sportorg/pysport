import logging
import threading
import time
import serial
from sportorg.lib.sportident import sireader


class SIReaderThread(threading.Thread):
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
        si = sireader.SIReaderReadout(port=self.port, debug=True)
        while True:
            try:
                while not si.poll_sicard():
                    time.sleep(0.5)
                    if not self.reading:
                        si.disconnect()
                        return
                # card_number = si.sicard
                # card_type = si.cardtype

                card_data = si.read_sicard()
                self.add_card_data(card_data)

                # beep
                si.ack_sicard()
            except sireader.SIReaderException as e:
                logging.debug(str(e))
            except sireader.SIReaderCardChanged as e:
                logging.debug(str(e))
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
        logging.debug('Available Ports')
        for i, p in enumerate(ports):
            logging.debug("{} - {}".format(i, p))

        return ports[0]
    else:
        logging.debug("No ports available")
        return None


if __name__ == '__main__':
    port = choose_port()
    if port is not None:
        reader = SIReaderThread(port)
        reader.start()
