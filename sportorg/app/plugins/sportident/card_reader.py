from . import sireader
from sportorg.core.event import event
from sportorg.app.models import memory


def read():
    return start()


def get_result(card_data):
    result = memory.Result()
    result.card_number = card_data['card_number']
    result.punches = card_data['punches']
    result.start_time = card_data['start']
    result.finish_time = card_data['finish']
    result.person = None

    return result


def start():
    port = sireader.choose_port()
    if port is not None:
        """
        :event: 'finish' 'sportident', result
        """
        reader = sireader.SIReaderThread(
            port,
            func=lambda card_data: event('finish', 'sportident', get_result(card_data))
        )
        reader.start()
        return reader

    return None


def stop(reader: sireader.SIReaderThread):
    print('close', reader)
    reader.stop()
