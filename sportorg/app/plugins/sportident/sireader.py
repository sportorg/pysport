import time
import json
import threading
from sportorg.lib.sportident import sireader
from sportorg.app.models import model


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
                control_cards = model.ControlCard.select().where(
                    model.ControlCard.name == 'SPORTIDENT',
                    model.ControlCard.value == card_number
                )
                if len(control_cards) == 0:
                    card = model.ControlCard.create(
                        name='SPORTIDENT',
                        value=card_number
                    )
                    model.Result.create(
                        control_card=card,
                        start_time=card_data['start'],
                        finish_time=card_data['finish'],
                        split_time=json.JSONEncoder().encode(card_data['punches'])
                    )

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
