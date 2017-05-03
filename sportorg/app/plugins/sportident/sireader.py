import time
import threading
from sportorg.lib.sportident import sireader


class SIReaderThread(threading.Thread):
    def __init__(self):
        super().__init__()
        print("init")

    def run(self):
        print("run")
        si = sireader.SIReaderReadout(port='COM3')
        while True:
            try:
                while not si.poll_sicard():
                    time.sleep(1)
                card_number = si.sicard
                card_type = si.cardtype

                card_data = si.read_sicard()
                print(card_number)
                print(card_type)
                print(card_data)
                # beep
                si.ack_sicard()
                if card_number == 1633208:
                    si.disconnect()
                    print("Exit")
                    break
            except sireader.SIReaderException as e:
                print(str(e))
            except sireader.SIReaderCardChanged as e:
                print(str(e))
            si.reconnect()

            time.sleep(0.5)


if __name__ == '__main__':
    reader = SIReaderThread()
    reader.start()
    print(reader.getName())

    print("end")
