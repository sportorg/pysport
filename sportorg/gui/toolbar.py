from sportorg import config
from sportorg.language import translate


def toolbar_list():
    return [
        (config.icon_dir("file.svg"), translate("New"), "NewAction"),
        (config.icon_dir("folder.svg"), translate("Open"), "OpenAction"),
        (config.icon_dir("save.svg"), translate("Save"), "SaveAction"),
        (
            config.icon_dir("form.svg"),
            translate("Event Settings"),
            "EventSettingsAction",
        ),
        (
            config.icon_dir("sportident.png"),
            translate("SPORTident readout"),
            "CardReadoutAction",
            "sportident",
        ),
        (
            config.icon_dir("network-off.svg"),
            translate("Teamwork"),
            "TeamworkEnableAction",
            "teamwork",
        ),
        (config.icon_dir("flag.svg"), translate("Manual finish"), "ManualFinishAction"),
    ]
