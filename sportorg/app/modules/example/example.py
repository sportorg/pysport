from sportorg.core import event


def import_action():
    print('import start')


def close():
    print('close plugin')


event.add_event('close', close)
