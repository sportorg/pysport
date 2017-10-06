import logging

from sportorg.app.controllers.global_access import GlobalAccess
from .sportident_properties import SportidentPropertiesDialog
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
            message(_('Cannot open port'), True)
    elif not reader.reading:
        reader = None
        start_reader()
    else:
        card_reader.stop(reader)
        if not reader.reading:
            port = reader.port
            reader = None
            message(_('Closing port' + ' ' + port))


def sportident_settings():
    try:
        SportidentPropertiesDialog().exec()
    except Exception as e:
        logging.exception(e)


def message(msg, is_error=False):
    logging.info(msg)
    GlobalAccess().get_main_window().statusbar.showMessage(msg, 5000)


event.add_event('finish', lambda _id, result: print(_id, result))
