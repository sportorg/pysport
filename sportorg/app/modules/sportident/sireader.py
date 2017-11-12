import logging
import threading
import time
import datetime
import serial
from sportorg.lib.sportident import sireader


class SIReaderThread(threading.Thread):
    def __init__(self, port, func=lambda card_data: card_data, start_time=None, debug=False):
        super().__init__()
        self.setName('SportidentThread')
        self.port = port
        self.readers = [func]
        self.cards = []
        self._reading = True
        self.start_time = start_time
        self.debug = debug

    @property
    def reading(self):
        return self._reading

    def add_card_data(self, card_data):
        for f in self.readers:
            thread = threading.Thread(
                target=f,
                args=(card_data,),
                name='Sportident-{}-Thread'.format(f.__name__))
            thread.start()
        self.cards.append(card_data)

    def run(self):
        si = sireader.SIReaderReadout(port=self.port, debug=self.debug)
        while True:
            try:
                while not si.poll_sicard():
                    time.sleep(0.5)
                    if not self.reading:
                        si.disconnect()
                        return
                # card_number = si.sicard

                card_data = si.read_sicard()
                # beep
                si.ack_sicard()

                card_data['card_type'] = si.cardtype
                card_data = self.check_data(card_data)
                self.add_card_data(card_data)

            except sireader.SIReaderException as e:
                logging.debug(str(e))
            except sireader.SIReaderCardChanged as e:
                logging.debug(str(e))
            except serial.serialutil.SerialException:
                self.stop()
                return
            except Exception as e:
                logging.exception(e)

    def check_data(self, card_data):
        if self.start_time and card_data['card_type'] == 'SI5':
            start_time = self.time_to_sec(self.start_time)
            for i in range(len(card_data['punches'])):
                if self.time_to_sec(card_data['punches'][i][1]) < start_time:
                    new_datetime = card_data['punches'][i][1].replace(hour=card_data['punches'][i][1].hour+12)
                    card_data['punches'][i] = (card_data['punches'][i][0], new_datetime)

        return card_data

    @staticmethod
    def time_to_sec(value, max_val=86400):
        if isinstance(value, datetime.datetime):
            ret = value.hour * 3600 + value.minute * 60 + value.second + value.microsecond / 1000000
            if max_val:
                ret = ret % max_val
            return ret

        return 0

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
