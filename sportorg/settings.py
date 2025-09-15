import os
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
    logging_window_row_count: int = 1000
    window_show_toolbar: bool = True
    window_dialog_path: str = ""
    window_geometry: str = ""
    race_use_birthday: bool = False
    templates_path: str = config.TEMPLATE_DIR
    file_autosave_interval: int = 300
    file_save_in_utf8: bool = False
    file_save_in_gzip: bool = True
    file_open_recent_file: bool = False
    file_recent: str = ""
    printer_main: str = ""
    printer_split: str = ""
    sound_enabled: bool = True
    sound_successful_path: Optional[str] = None
    sound_unsuccessful_path: Optional[str] = None
    sound_rented_card_enabled: bool = True
    sound_rented_card_path: Optional[str] = None
    sound_enter_number_path: Optional[str] = None
    ranking: Dict[str, Any] = field(default_factory=dict)
    live_gzip_enabled: bool = True

    telegram_token: str = ""

    source_names_path: str = config.base_dir("configs", "names.txt")
    source_middle_names_path: str = config.base_dir("configs", "middle_names.txt")
    source_regions_path: str = config.base_dir("configs", "regions.txt")
    source_status_comments_path: str = config.base_dir("configs", "status_comments.txt")
    source_status_default_comments_path: str = config.base_dir(
        "configs", "status_default.txt"
    )
    source_ranking_score_path: str = config.base_dir("configs", "ranking.txt")
    source_rent_cards_path: str = config.data_dir("rent_cards.txt")


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


def template_dir(*paths) -> str:
    return os.path.join(SETTINGS.templates_path, *paths)
