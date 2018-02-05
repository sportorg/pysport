from sportorg import config
from sportorg.language import _


def toolbar_list():
    return [
        (config.icon_dir('file.png'), _('New'), 'NewAction'),
        (config.icon_dir('folder.png'), _('Open'), 'OpenAction'),
        (config.icon_dir('save.png'), _('Save'), 'SaveAction'),
        (config.icon_dir('sportident.png'), _('SPORTident readout'), 'SPORTidentReadoutAction'),
        (config.icon_dir('flag.png'), _('Manual finish'), 'ManualFinishAction'),
        (config.icon_dir('repeat.png'), _('Teamwork'), 'TeamworkEnableAction'),
    ]
