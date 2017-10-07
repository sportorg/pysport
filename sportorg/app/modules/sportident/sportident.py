import logging

from sportorg.app.gui.global_access import GlobalAccess
from . import card_reader
from sportorg.core import event
from sportorg.language import _


reader = None


def start_reader():
    global reader
    if reader is None:
        reader = card_reader.read()
        if reader is not None:
            message(_('Opening port') + ' ' + reader.port)
        else:
            message(_('Cannot open port'))
    elif not reader.reading:
        reader = None
        start_reader()
    else:
        card_reader.stop(reader)
        if not reader.reading:
            port = reader.port
            reader = None
            message(_('Closing port' + ' ' + port))


def message(msg):
    logging.info(msg)
    GlobalAccess().get_main_window().statusbar.showMessage(msg, 5000)


event.add_event('finish', lambda _id, result: print(_id, result))
