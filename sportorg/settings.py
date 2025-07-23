from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from sportorg import config
from sportorg.libs.settings import load_settings, save_settings


@dataclass
class Settings:
    app_check_updates: bool = True
    locale: str = "ru_RU"
    logging_level: str = "INFO"
    logging_window_row_count = 1000
    window_show_toolbar: bool = True
    window_dialog_path: str = ""
    window_geometry: str = ""
    race_use_birthday: bool = False
    templates_path: str = ""
    file_autosave_interval = 0
    file_save_in_utf8: bool = False
    file_save_in_gzip: bool = True
    file_open_recent_file: bool = False
    file_recent: str = ""
    printer_main: str = ""
    printer_split: str = ""
    sound_enabled: bool = True
    sound_successful_path: Optional[str] = None
    sound_unsuccessful_path: Optional[str] = None
    sound_enabled_rented_card: bool = True
    sound_rented_card_path: Optional[str] = None
    sound_enter_number_path: Optional[str] = None
    ranking: Dict[str, Any] = field(default_factory=dict)


SETTINGS = Settings()


def set_settings(settings: Settings) -> None:
    global SETTINGS
    SETTINGS = settings


def load_settings_from_file(path: str = config.SETTINGS_JSON) -> Tuple[Settings, bool]:
    loaded_settings = load_settings(Path(path), Settings)
    if loaded_settings is not None:
        set_settings(loaded_settings)
        return SETTINGS, True

    return SETTINGS, False


def save_settings_to_file(path: str = config.SETTINGS_JSON) -> None:
    save_settings(SETTINGS, Path(path))
