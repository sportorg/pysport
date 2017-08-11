from sportorg.core import event


def import_action():
    print('import start')


def menu():
    return ['Example', import_action]

event.add_event('menu_file_import', menu)
