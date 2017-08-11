from . import card_reader
from sportorg import config
from sportorg.core import event

reader = None


def _(string):
    return string


def start_reader():
    global reader
    if reader is None:
        reader = card_reader.read()
        if reader is not None:
            print(_('Open port ' + reader.port), 5000)
            f_id = reader.append_reader(lambda data: print('from main.py', data))
            # reader.delete_func(f_id)
        else:
            print(_('Port not open'), 5000)
    elif not reader.reading:
        reader = None
        start_reader()
    else:
        card_reader.stop(reader)
        if not reader.reading:
            port = reader.port
            reader = None
            print(_('Close port ' + port), 5000)


def toolbar():
    return [config.plugin_dir('sportident', 'img', 'sportident.png'), _("SPORTident readout"), start_reader]

event.add_event('toolbar', toolbar)

