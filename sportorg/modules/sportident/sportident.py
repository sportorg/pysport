import logging

from sportorg.language import _
from . import card_reader

reader = None


def is_readout():
    return reader is not None


def start_reader():
    global reader
    if not is_readout():
        reader = card_reader.start()
        if is_readout():
            logging.info(_('Opening port') + ' ' + reader.port)
        else:
            logging.info(_('Cannot open port'))
    elif not reader.reading:
        reader = None
        start_reader()
    else:
        card_reader.stop(reader)
        if not reader.reading:
            port = reader.port
            reader = None
            logging.info(_('Closing port') + ' ' + port)
