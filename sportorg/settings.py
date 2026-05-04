import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from sportorg import config
from sportorg.libs.settings import load_settings, save_settings

FEATURE_SFR = "sfr"
FEATURE_SPORTIDENT = "sportident"
FEATURE_SPORTIDUINO = "sportiduino"
FEATURE_RFID_IMPINJ = "rfid_impinj"
FEATURE_SRPID = "srpid"
FEATURE_HUICHANG = "huichang"
FEATURE_WINORIENT = "winorient"
FEATURE_TELEGRAM = "telegram"
DEFAULT_FEATURES = {
    FEATURE_SPORTIDENT: True,
    FEATURE_SFR: True,
    FEATURE_SPORTIDUINO: True,
    FEATURE_RFID_IMPINJ: True,
    FEATURE_SRPID: True,
    FEATURE_HUICHANG: True,
    FEATURE_WINORIENT: True,
    FEATURE_TELEGRAM: True,
}


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
    templates_settings: Dict[str, Any] = field(default_factory=dict)
    file_autosave_interval: int = 300
    file_save_in_utf8: bool = False
    file_save_in_gzip: bool = True
    file_generate_srb: bool = False
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
    ranking_ardf: Dict[str, Any] = field(default_factory=dict)
    live_gzip_enabled: bool = True
    features: Dict[str, bool] = field(default_factory=lambda: DEFAULT_FEATURES.copy())

    telegram_token: str = ""
    teamwork_host: str = "localhost"
    teamwork_port: int = 50010
    teamwork_type_connection: str = "client"
    teamwork_encryption_enabled: bool = False
    teamwork_autorun: bool = False
    teamwork_encryption_key: str = ""
    teamwork_check_race_id: bool = False

    source_names_path: str = config.configs_dir("names.txt")
    source_middle_names_path: str = config.configs_dir("middle_names.txt")
    source_regions_path: str = config.configs_dir("regions.txt")
    source_status_comments_path: str = config.configs_dir("status_comments.txt")
    source_status_default_comments_path: str = config.configs_dir("status_default.txt")
    source_ranking_score_path: str = config.configs_dir("ranking.txt")
    source_ranking_ardf_score_path: str = config.configs_dir("ranking_ardf.txt")
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


def get_feature_flags() -> Dict[str, bool]:
    feature_flags = DEFAULT_FEATURES.copy()
    stored_features = SETTINGS.features if isinstance(SETTINGS.features, dict) else {}
    feature_flags.update(stored_features)
    return feature_flags


def is_feature_enabled(feature: str) -> bool:
    return bool(get_feature_flags().get(feature, True))


def set_feature_enabled(feature: str, enabled: bool) -> None:
    SETTINGS.features = get_feature_flags()
    SETTINGS.features[feature] = bool(enabled)


def template_dir(*paths) -> str:
    return os.path.join(SETTINGS.templates_path, *paths)
