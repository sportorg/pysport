from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _


def toolbar_list():
    """

    :return: [(icon -> str, title -> str, action -> func, property? -> str)...]
    """
    return [
        (config.icon_dir('file.png'), _('New'), GlobalAccess().get_main_window().create_file),
        (config.icon_dir('folder.png'), _('Open'), GlobalAccess().get_main_window().open_file_dialog),
        (config.icon_dir('save.png'), _('Save'), GlobalAccess().get_main_window().save_file),
        (config.icon_dir('sportident.png'), _('SPORTident readout'),
         GlobalAccess().get_main_window().sportident_connect, 'sportident'),
        (config.icon_dir('flag.png'), _('Manual finish'), GlobalAccess().get_main_window().manual_finish),
    ]
