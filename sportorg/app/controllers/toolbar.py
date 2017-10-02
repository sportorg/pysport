from sportorg import config
from sportorg.language import _
from sportorg.app.controllers.global_access import GlobalAccess


def toolbar_list():
    return [
        (config.icon_dir("file.png"), _("New"), GlobalAccess().get_main_window().create_file),
        (config.icon_dir("folder.png"), _("Open"), GlobalAccess().get_main_window().open_file),
        (config.icon_dir("save.png"), _("Save"), GlobalAccess().get_main_window().save_file),
    ]
