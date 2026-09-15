import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sportorg import config, paths
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

# Bumped whenever stored settings need a one-time fix-up on load.
CURRENT_SETTINGS_VERSION = 2


@dataclass
class Settings:
    # 1 means "written before path settings became app-relative".  The
    # default has to be the legacy value: a key missing from settings.json
    # falls back to it, and that is exactly the file we need to migrate.
    settings_version: int = 1
    app_check_updates: bool = True
    theme: str = "system"
    locale: str = "ru_RU"
    logging_level: str = "INFO"
    logging_window_row_count: int = 1000
    window_show_toolbar: bool = True
    window_dialog_path: str = ""
    window_geometry: str = ""
    race_use_birthday: bool = False
    templates_path: str = ""
    templates_settings: Dict[str, Any] = field(default_factory=dict)
    file_autosave_interval: int = 300
    file_save_in_utf8: bool = True
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
    plugins: List[Dict[str, Any]] = field(default_factory=list)
    plugin_settings: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    telegram_token: str = ""
    teamwork_host: str = "localhost"
    teamwork_port: int = 50010
    teamwork_type_connection: str = "client"
    teamwork_encryption_enabled: bool = False
    teamwork_autorun: bool = False
    teamwork_encryption_key: str = ""
    teamwork_check_race_id: bool = False

    source_names_path: str = ""
    source_middle_names_path: str = ""
    source_countries_path: str = ""
    source_groups_path: str = ""
    source_regions_path: str = ""
    source_status_comments_path: str = ""
    source_status_default_comments_path: str = ""
    source_ranking_score_path: str = ""
    source_ranking_ardf_score_path: str = ""
    source_rent_cards_path: str = ""


SETTINGS = Settings()


def set_settings(settings: Settings) -> None:
    global SETTINGS
    SETTINGS = settings


def configs_dir(*parts: str) -> str:
    return paths.resolve_seeded("configs", *parts)


def template_dir(*parts: str) -> str:
    return paths.resolve_seeded(
        "templates", *parts, override=SETTINGS.templates_path or config.TEMPLATES_PATH
    )


def names_path() -> str:
    return SETTINGS.source_names_path or configs_dir("names.txt")


def middle_names_path() -> str:
    return SETTINGS.source_middle_names_path or configs_dir("middle_names.txt")


def countries_path() -> str:
    return SETTINGS.source_countries_path or configs_dir("countries.txt")


def groups_path() -> str:
    return SETTINGS.source_groups_path or configs_dir("groups.txt")


def regions_path() -> str:
    return SETTINGS.source_regions_path or configs_dir("regions.txt")


def status_comments_path() -> str:
    return SETTINGS.source_status_comments_path or configs_dir("status_comments.txt")


def status_default_comments_path() -> str:
    return SETTINGS.source_status_default_comments_path or configs_dir(
        "status_default.txt"
    )


def ranking_score_path() -> str:
    return SETTINGS.source_ranking_score_path or configs_dir("ranking.txt")


def ranking_ardf_score_path() -> str:
    return SETTINGS.source_ranking_ardf_score_path or configs_dir("ranking_ardf.txt")


def rent_cards_path() -> str:
    return SETTINGS.source_rent_cards_path or config.data_dir("rent_cards.txt")


# The sound fields use None as their sentinel, so the shipped file has to be
# resolved on read rather than written into settings.json on first run.
def successful_sound_path() -> str:
    return SETTINGS.sound_successful_path or config.sound_dir("ok.wav")


def unsuccessful_sound_path() -> str:
    return SETTINGS.sound_unsuccessful_path or config.sound_dir("failure.wav")


def rented_card_sound_path() -> str:
    return SETTINGS.sound_rented_card_path or config.sound_dir("rented_card.wav")


def enter_number_sound_path() -> str:
    return SETTINGS.sound_enter_number_path or config.sound_dir("enter_number.wav")


# The shape each field had while paths were stored absolutely, as trailing
# path segments.  A value matching one of these is a former default rather
# than something the operator chose.
_FORMER_DEFAULTS: Dict[str, Tuple[Tuple[str, ...], ...]] = {
    "templates_path": (("sportorg", "data", "templates"), ("templates",)),
    "source_names_path": (("configs", "names.txt"),),
    "source_middle_names_path": (("configs", "middle_names.txt"),),
    "source_countries_path": (("configs", "countries.txt"),),
    "source_groups_path": (("configs", "groups.txt"),),
    "source_regions_path": (("configs", "regions.txt"),),
    "source_status_comments_path": (("configs", "status_comments.txt"),),
    "source_status_default_comments_path": (("configs", "status_default.txt"),),
    "source_ranking_score_path": (("configs", "ranking.txt"),),
    "source_ranking_ardf_score_path": (("configs", "ranking_ardf.txt"),),
    "source_rent_cards_path": (("data", "rent_cards.txt"),),
}


def _ends_with_segments(value: str, tail: Tuple[str, ...]) -> bool:
    segments = [s for s in value.replace("\\", "/").split("/") if s]
    if len(segments) < len(tail):
        return False

    return [s.lower() for s in segments[-len(tail) :]] == [t.lower() for t in tail]


def sanitize_path(field_name: str, value: str) -> str:
    """Replace a dead former-default path with the empty sentinel.

    Both halves of the test are needed.  Clearing every missing path would
    discard a network location that merely happens to be offline; clearing
    every default-shaped path would discard a directory the operator picked
    by hand that resolves fine.  Together they identify exactly the paths
    left dangling by an installation that used to resolve them from the
    working directory.
    """
    if not value or os.path.exists(value):
        return value

    for tail in _FORMER_DEFAULTS.get(field_name, ()):
        if _ends_with_segments(value, tail):
            logging.info("Clearing stale %s: %s", field_name, value)
            return ""

    return value


def _migrate_paths(settings: Settings) -> None:
    for field_name in _FORMER_DEFAULTS:
        value = getattr(settings, field_name, "")
        if isinstance(value, str):
            setattr(settings, field_name, sanitize_path(field_name, value))


def load_settings_from_file(path: Optional[str] = None) -> Tuple[Settings, bool]:
    path = path or config.SETTINGS_JSON
    loaded_settings = load_settings(Path(path), Settings)
    if loaded_settings is not None:
        set_settings(loaded_settings)
        if SETTINGS.settings_version < CURRENT_SETTINGS_VERSION:
            _migrate_paths(SETTINGS)
            SETTINGS.settings_version = CURRENT_SETTINGS_VERSION
            save_settings_to_file(path)
        return SETTINGS, True

    SETTINGS.settings_version = CURRENT_SETTINGS_VERSION
    return SETTINGS, False


def save_settings_to_file(path: Optional[str] = None) -> None:
    save_settings(SETTINGS, Path(path or config.SETTINGS_JSON))


def load_settings_on_startup() -> None:
    """Load settings.json, or produce one on a first run."""
    _, exists = load_settings_from_file()
    if exists:
        return

    if os.path.exists(config.CONFIG_INI):
        import_legacy_config()

    save_settings_to_file()


def import_legacy_config() -> None:
    """Carry the pre-1.6 config.ini over into settings.json."""
    from sportorg.modules.configs.configs import Config, ConfigFile

    Config().read()
    SETTINGS.app_check_updates = Config().configuration.get("check_updates", True)
    SETTINGS.locale = Config().configuration.get("current_locale", "ru_RU")
    SETTINGS.logging_level = Config().configuration.get("logging_level", "INFO")
    SETTINGS.logging_window_row_count = Config().configuration.get(
        "log_window_row_count", 1000
    )
    SETTINGS.window_show_toolbar = Config().configuration.get("show_toolbar", True)
    SETTINGS.window_geometry = Config().geometry.get("main", "01")
    SETTINGS.window_dialog_path = Config().parser.get(
        ConfigFile.DIRECTORY, "dialog_default_dir", fallback=""
    )
    SETTINGS.race_use_birthday = Config().configuration.get("use_birthday", False)
    SETTINGS.templates_path = sanitize_path(
        "templates_path", Config().templates.get("directory", "")
    )
    SETTINGS.file_autosave_interval = Config().configuration.get("autosave_interval", 0)
    SETTINGS.file_save_in_utf8 = Config().configuration.get("save_in_utf8", True)
    SETTINGS.file_save_in_gzip = Config().configuration.get("save_in_gzip", True)
    SETTINGS.file_generate_srb = Config().configuration.get("generate_srb", True)
    SETTINGS.file_open_recent_file = Config().configuration.get(
        "open_recent_file", True
    )
    SETTINGS.printer_main = Config().printer.get("main", "")
    SETTINGS.printer_split = Config().printer.get("split", "")
    SETTINGS.sound_enabled = Config().sound.get("enabled", False)
    SETTINGS.sound_successful_path = Config().sound.get("successful")
    SETTINGS.sound_unsuccessful_path = Config().sound.get("unsuccessful")
    SETTINGS.sound_rented_card_enabled = Config().sound.get("enabled_rented_card", True)
    SETTINGS.sound_rented_card_path = Config().sound.get("rented_card")
    SETTINGS.sound_enter_number_path = Config().sound.get("enter_number")
    SETTINGS.ranking = Config().ranking.get_all() or {}
    SETTINGS.ranking_ardf = Config().ranking_ardf.get_all() or {}


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


def get_plugin_configs() -> List[Dict[str, Any]]:
    raw_plugins = SETTINGS.plugins if isinstance(SETTINGS.plugins, list) else []
    plugin_configs = []
    for item in raw_plugins:
        if not isinstance(item, dict):
            continue

        executable_path = str(item.get("executable_path", item.get("path", "")))
        arguments = str(item.get("arguments", ""))
        plugin_id = str(item.get("plugin_id", ""))
        plugin_configs.append(
            {
                "executable_path": executable_path,
                "arguments": arguments,
                "enabled": bool(item.get("enabled", False)),
                "plugin_id": plugin_id,
            }
        )
    return plugin_configs


def set_plugin_configs(plugin_configs: List[Dict[str, Any]]) -> None:
    SETTINGS.plugins = []
    for item in plugin_configs:
        if not isinstance(item, dict):
            continue
        SETTINGS.plugins.append(
            {
                "executable_path": str(item.get("executable_path", "")),
                "arguments": str(item.get("arguments", "")),
                "enabled": bool(item.get("enabled", False)),
                "plugin_id": str(item.get("plugin_id", "")),
            }
        )


def set_plugin_config_plugin_id(index: int, plugin_id: str) -> None:
    plugin_configs = get_plugin_configs()
    if index < 0 or index >= len(plugin_configs):
        return

    plugin_configs[index]["plugin_id"] = plugin_id
    set_plugin_configs(plugin_configs)


def get_plugin_saved_settings(plugin_id: str) -> Dict[str, Any]:
    if not plugin_id or not isinstance(SETTINGS.plugin_settings, dict):
        return {}

    plugin_data = SETTINGS.plugin_settings.get(plugin_id, {})
    if isinstance(plugin_data, dict):
        return plugin_data.copy()
    return {}


def set_plugin_saved_settings(plugin_id: str, plugin_data: Dict[str, Any]) -> None:
    if not plugin_id:
        return

    if not isinstance(SETTINGS.plugin_settings, dict):
        SETTINGS.plugin_settings = {}

    SETTINGS.plugin_settings[plugin_id] = plugin_data.copy()
