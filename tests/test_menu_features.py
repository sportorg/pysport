import importlib.util
from pathlib import Path

from sportorg import settings


def _load_menu_module():
    menu_path = Path(__file__).parents[1] / "sportorg" / "gui" / "menu" / "menu.py"
    spec = importlib.util.spec_from_file_location("test_menu_module", menu_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _action_names(menu_items):
    names = []
    for item in menu_items:
        if "action" in item:
            names.append(item["action"])
        if "actions" in item:
            names.extend(_action_names(item["actions"]))
    return names


def test_sfr_menu_items_visible_by_default():
    old_features = settings.SETTINGS.features
    try:
        settings.SETTINGS.features = {}

        assert "SFRXImportAction" in _action_names(_load_menu_module().menu_list())
    finally:
        settings.SETTINGS.features = old_features


def test_sfr_menu_items_hidden_when_feature_disabled():
    old_features = settings.SETTINGS.features
    try:
        settings.set_feature_enabled(settings.FEATURE_SFR, False)

        assert "SFRXImportAction" not in _action_names(_load_menu_module().menu_list())
    finally:
        settings.SETTINGS.features = old_features
