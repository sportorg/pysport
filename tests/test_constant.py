from sportorg import settings
from sportorg.models.constant import Countries, Groups, get_countries, get_groups


def test_get_countries_loads_from_config_file(tmp_path, monkeypatch):
    countries_file = tmp_path / "countries.txt"
    countries_file.write_text("France\nJapan\n", encoding="utf-8")
    countries = Countries()
    old_items = list(countries.get_all())
    old_loaded = countries._LOADED

    try:
        monkeypatch.setattr(
            settings.SETTINGS, "source_countries_path", str(countries_file)
        )
        countries.COUNTRIES = []
        countries._LOADED = False

        assert get_countries() == ["", "France", "Japan"]
    finally:
        countries.COUNTRIES = old_items
        countries._LOADED = old_loaded


def test_get_groups_loads_from_config_file(tmp_path, monkeypatch):
    groups_file = tmp_path / "groups.txt"
    groups_file.write_text("M21\nD21\n", encoding="utf-8")
    groups = Groups()
    old_items = list(groups.get_all())
    old_loaded = groups._LOADED

    try:
        monkeypatch.setattr(settings.SETTINGS, "source_groups_path", str(groups_file))
        groups.GROUPS = []
        groups._LOADED = False

        assert get_groups() == ["", "M21", "D21"]
    finally:
        groups.GROUPS = old_items
        groups._LOADED = old_loaded
