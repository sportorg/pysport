"""A first run must not quietly replace the shipped defaults.

Startup doubles as the importer for the pre-1.6 `config.ini`. It used to run
that import unconditionally, and `Config()` answers every question with its
own legacy defaults, so a fresh installation came up with settings nobody had
chosen.
"""

import json

import pytest

from sportorg import config, settings
from sportorg.modules.configs.configs import Config

LEGACY_CONFIG_INI = """\
[configuration]
autosave_interval = 42
save_in_utf8 = True

[sound]
enabled = True
"""


@pytest.fixture
def install(tmp_path, monkeypatch):
    """An empty {app}/data with no settings.json and no config.ini."""
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setattr(config, "SETTINGS_JSON", str(data / "settings.json"))
    monkeypatch.setattr(config, "CONFIG_INI", str(data / "config.ini"))
    monkeypatch.setattr(settings, "SETTINGS", settings.Settings())
    Config._instances = {}
    yield data
    Config._instances = {}


def stored(data):
    return json.loads((data / "settings.json").read_text(encoding="utf-8"))


def test_first_run_without_config_ini_keeps_the_shipped_defaults(install):
    settings.load_settings_on_startup()

    assert settings.SETTINGS.file_autosave_interval == 300
    assert settings.SETTINGS.file_save_in_utf8 is True
    assert settings.SETTINGS.file_generate_srb is False
    assert settings.SETTINGS.sound_enabled is True
    assert settings.SETTINGS.sound_successful_path is None


def test_first_run_writes_settings_json(install):
    settings.load_settings_on_startup()

    assert stored(install)["file_autosave_interval"] == 300
    assert stored(install)["settings_version"] == settings.CURRENT_SETTINGS_VERSION


def test_sound_paths_resolve_from_the_package_rather_than_being_stored(install):
    settings.load_settings_on_startup()

    assert "settings_json" not in stored(install)
    assert stored(install)["sound_successful_path"] is None
    assert settings.successful_sound_path().endswith("ok.wav")


def test_legacy_config_ini_is_still_imported(install):
    (install / "config.ini").write_text(LEGACY_CONFIG_INI, encoding="utf-8")

    settings.load_settings_on_startup()

    assert settings.SETTINGS.file_autosave_interval == 42
    assert settings.SETTINGS.file_save_in_utf8 is True
    assert settings.SETTINGS.sound_enabled is True


def test_existing_settings_json_is_not_overwritten_by_config_ini(install):
    (install / "config.ini").write_text(LEGACY_CONFIG_INI, encoding="utf-8")
    (install / "settings.json").write_text(
        json.dumps({"file_autosave_interval": 600}), encoding="utf-8"
    )

    settings.load_settings_on_startup()

    assert settings.SETTINGS.file_autosave_interval == 600
