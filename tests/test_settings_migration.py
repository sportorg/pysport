import json
import os

import pytest

from sportorg import settings


@pytest.fixture
def fresh_settings(monkeypatch):
    monkeypatch.setattr(settings, "SETTINGS", settings.Settings())
    return settings.SETTINGS


def write_settings(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def read_settings(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_legacy_file_is_migrated(tmp_path, fresh_settings):
    path = tmp_path / "settings.json"
    dead = tmp_path / "elsewhere" / "configs" / "countries.txt"
    write_settings(path, {"source_countries_path": str(dead)})

    loaded, exists = settings.load_settings_from_file(str(path))

    assert exists
    assert loaded.source_countries_path == ""
    assert loaded.settings_version == settings.CURRENT_SETTINGS_VERSION
    stored = read_settings(path)
    assert stored["settings_version"] == settings.CURRENT_SETTINGS_VERSION
    assert stored["source_countries_path"] == ""


def test_live_path_is_kept(tmp_path, fresh_settings):
    path = tmp_path / "settings.json"
    live = tmp_path / "configs" / "countries.txt"
    live.parent.mkdir()
    live.write_text("France\n", encoding="utf-8")
    write_settings(path, {"source_countries_path": str(live)})

    loaded, _ = settings.load_settings_from_file(str(path))

    assert loaded.source_countries_path == str(live)


def test_offline_user_path_is_kept(tmp_path, fresh_settings):
    path = tmp_path / "settings.json"
    unreachable = os.path.join("\\\\server", "share", "my-templates")
    write_settings(path, {"templates_path": unreachable})

    loaded, _ = settings.load_settings_from_file(str(path))

    assert loaded.templates_path == unreachable


def test_dead_default_template_dir_is_cleared(tmp_path, fresh_settings):
    path = tmp_path / "settings.json"
    dead = tmp_path / "gone" / "sportorg" / "data" / "templates"
    write_settings(path, {"templates_path": str(dead)})

    loaded, _ = settings.load_settings_from_file(str(path))

    assert loaded.templates_path == ""


def test_migration_does_not_repeat(tmp_path, fresh_settings):
    path = tmp_path / "settings.json"
    dead = tmp_path / "elsewhere" / "configs" / "countries.txt"
    write_settings(
        path,
        {
            "settings_version": settings.CURRENT_SETTINGS_VERSION,
            "source_countries_path": str(dead),
        },
    )

    loaded, _ = settings.load_settings_from_file(str(path))

    assert loaded.source_countries_path == str(dead)


def test_first_run_records_the_current_version(tmp_path, fresh_settings):
    _, exists = settings.load_settings_from_file(str(tmp_path / "settings.json"))

    assert not exists
    assert settings.SETTINGS.settings_version == settings.CURRENT_SETTINGS_VERSION


def test_override_is_used_verbatim(fresh_settings, monkeypatch):
    monkeypatch.setattr(
        fresh_settings, "source_ranking_score_path", os.path.join("D:", "ranking.txt")
    )

    assert settings.ranking_score_path() == os.path.join("D:", "ranking.txt")


def test_empty_resolves_from_the_program_directory(fresh_settings):
    assert settings.ranking_score_path().endswith(
        os.path.join("configs", "ranking.txt")
    )
    assert settings.rent_cards_path().endswith(os.path.join("data", "rent_cards.txt"))
    assert os.path.isdir(settings.template_dir())
    assert os.path.isfile(settings.ranking_score_path())
