from . import sireader
from sportorg.core.event import event


def read():
    return start()


def start():
    port = sireader.choose_port()
    if port is not None:
        """
        :event: 'finish' card_data
        """
        reader = sireader.SIReaderThread(port, func=lambda card_data: event('finish', card_data))
        reader.start()
        return reader

    return None


def stop(reader: sireader.SIReaderThread):
    print('close', reader)
    reader.stop()
