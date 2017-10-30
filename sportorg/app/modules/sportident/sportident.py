import logging

from sportorg.app.gui.global_access import GlobalAccess
from . import card_reader
from sportorg.language import _


reader = None


def is_readout():
    return reader is not None


def start_reader():
    global reader
    if not is_readout():
        reader = card_reader.read()
        if is_readout():
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

    toolbar_sportident()


def message(msg):
    logging.info(msg)
    GlobalAccess().get_main_window().statusbar.showMessage(msg, 5000)


def toolbar_sportident():
    GlobalAccess().get_main_window().toolbar_property['sportident'].setStatusTip(
        _('SPORTident readout activated') if is_readout() else _('SPORTident readout not activated'))
