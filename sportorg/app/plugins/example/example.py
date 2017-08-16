from sportorg.core import event


def import_action():
    print('import start')


def menu():
    return ['Example', import_action]


def close():
    print('close plugin')

event.add_event('menu_file_import', menu)
event.add_event('close', close)
