import traceback
import logging

from .sportident_properties import SportidentPropertiesDialog
from . import card_reader
from sportorg import config
from sportorg.core import event

reader = None
statusbar = None


def _(string):
    return string


def start_reader():
    global reader
    if reader is None:
        reader = card_reader.read()
        if reader is not None:
            message(_('Open port ' + reader.port))
        else:
            message(_('Port not open'), True)
    elif not reader.reading:
        reader = None
        start_reader()
    else:
        card_reader.stop(reader)
        if not reader.reading:
            port = reader.port
            reader = None
            message(_('Close port ' + port))


def sportident_settings():
    try:
        SportidentPropertiesDialog().exec()
    except:
        traceback.print_exc()


def toolbar():
    return [config.plugin_dir('sportident', 'img', 'sportident.png'), _("SPORTident readout"), start_reader]


def menu_setting():
    return [_('SPORTident settings'), sportident_settings]


def set_statusbar(sb):
    global statusbar
    statusbar = sb


def message(msg, is_error=False):
    if is_error:
        logging.error(msg)
    else:
        logging.info(msg)
    statusbar.showMessage(msg, 5000)


event.add_event('toolbar', toolbar)
event.add_event('menuoptions', menu_setting)
event.add_event('statusbar', set_statusbar)
event.add_event('finish', lambda _id, result: print(_id, result))
