import importlib.util
from pathlib import Path

import pytest

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


def test_punch_system_features_enabled_by_default():
    old_features = settings.SETTINGS.features
    try:
        settings.SETTINGS.features = {}

        for feature in (
            settings.FEATURE_SPORTIDENT,
            settings.FEATURE_SFR,
            settings.FEATURE_SPORTIDUINO,
            settings.FEATURE_RFID_IMPINJ,
            settings.FEATURE_SRPID,
            settings.FEATURE_HUICHANG,
        ):
            assert settings.is_feature_enabled(feature)
    finally:
        settings.SETTINGS.features = old_features


def test_feature_menu_items_visible_by_default():
    old_features = settings.SETTINGS.features
    try:
        settings.SETTINGS.features = {}
        action_names = _action_names(_load_menu_module().menu_list())

        assert "SFRXImportAction" in action_names
        assert "SFRExportAction" in action_names
        assert "HuichangManagementAction" in action_names
        assert "AddSPORTidentResultAction" in action_names
        assert "CSVWinorientImportAction" in action_names
        assert "TelegramSendAction" in action_names
        assert "TelegramSettingsAction" in action_names
    finally:
        settings.SETTINGS.features = old_features


@pytest.mark.parametrize(
    ("feature", "actions"),
    [
        (
            settings.FEATURE_SFR,
            ("SFRXImportAction", "SFRExportAction"),
        ),
        (
            settings.FEATURE_HUICHANG,
            ("HuichangManagementAction",),
        ),
        (
            settings.FEATURE_SPORTIDENT,
            (
                "AddSPORTidentResultAction",
                "RecoverySportidentMasterCsvAction",
                "RecoverySportorgSiLogAction",
            ),
        ),
        (
            settings.FEATURE_WINORIENT,
            (
                "CSVWinorientImportAction",
                "WDBWinorientImportAction",
                "WDBWinorientExportAction",
            ),
        ),
        (
            settings.FEATURE_TELEGRAM,
            ("TelegramSendAction", "TelegramSettingsAction"),
        ),
    ],
)
def test_menu_items_hidden_when_feature_disabled(feature, actions):
    old_features = settings.SETTINGS.features
    try:
        settings.set_feature_enabled(feature, False)
        action_names = _action_names(_load_menu_module().menu_list())

        for action in actions:
            assert action not in action_names
    finally:
        settings.SETTINGS.features = old_features
