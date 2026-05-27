import json
from pathlib import Path

from sportorg import settings as settings_module
from sportorg.settings import (
    Settings,
    load_settings_from_file,
    save_settings_to_file,
    set_settings,
)


def test_settings_default_theme_is_system():
    fresh = Settings()
    assert fresh.theme == "system"


def test_settings_round_trip_preserves_theme(tmp_path: Path):
    set_settings(Settings())
    settings_module.SETTINGS.theme = "dark"
    target = tmp_path / "settings.json"
    save_settings_to_file(str(target))
    set_settings(Settings())
    assert settings_module.SETTINGS.theme == "system"
    load_settings_from_file(str(target))
    assert settings_module.SETTINGS.theme == "dark"


def test_settings_load_without_theme_key_falls_back_to_default(tmp_path: Path):
    target = tmp_path / "settings.json"
    target.write_text(json.dumps({"locale": "ru_RU"}), encoding="utf-8")
    set_settings(Settings())
    load_settings_from_file(str(target))
    assert settings_module.SETTINGS.theme == "system"
