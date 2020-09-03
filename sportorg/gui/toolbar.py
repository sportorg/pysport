from sportorg import config
from sportorg.language import _


def toolbar_list():
    return [
        (config.icon_dir('file.svg'), _('New'), 'NewAction'),
        (config.icon_dir('folder.svg'), _('Open'), 'OpenAction'),
        (config.icon_dir('save.svg'), _('Save'), 'SaveAction'),
        (config.icon_dir('form.svg'), _('Event Settings'), 'EventSettingsAction'),
        (
            config.icon_dir('sportident.png'),
            _('SPORTident readout'),
            'SPORTidentReadoutAction',
            'sportident',
        ),
        (
            config.icon_dir('network-off.svg'),
            _('Teamwork'),
            'TeamworkEnableAction',
            'teamwork',
        ),
        (config.icon_dir('flag.svg'), _('Manual finish'), 'ManualFinishAction'),
    ]
