import sys

import pytest

from sportorg.gui import theme


def test_theme_constants_exposed():
    assert theme.THEME_SYSTEM == "system"
    assert theme.THEME_LIGHT == "light"
    assert theme.THEME_DARK == "dark"
    assert theme.VALID_THEMES == {"system", "light", "dark"}


def test_build_light_palette_returns_default_qpalette():
    try:
        from PySide6.QtGui import QPalette
    except ModuleNotFoundError:
        from PySide2.QtGui import QPalette

    palette = theme._build_light_palette()
    assert isinstance(palette, QPalette)


def test_build_light_palette_window_color():
    # Light palette must be deterministically light regardless of OS color
    # scheme. On Qt 6.5+ Windows 11 dark mode, both QPalette() and
    # QStyle.standardPalette() return a dark palette — that is the regression
    # this test guards against.
    try:
        from PySide6.QtGui import QColor, QPalette
    except ModuleNotFoundError:
        from PySide2.QtGui import QColor, QPalette

    palette = theme._build_light_palette()
    assert palette.color(QPalette.Active, QPalette.Window) == QColor(239, 239, 239)
    assert palette.color(QPalette.Active, QPalette.WindowText) == QColor(0, 0, 0)
    assert palette.color(QPalette.Active, QPalette.Base) == QColor(255, 255, 255)
    assert palette.color(QPalette.Active, QPalette.Text) == QColor(0, 0, 0)
    assert palette.color(QPalette.Active, QPalette.Button) == QColor(239, 239, 239)
    assert palette.color(QPalette.Disabled, QPalette.Text) == QColor(190, 190, 190)


def test_build_dark_palette_window_color():
    try:
        from PySide6.QtGui import QColor, QPalette
    except ModuleNotFoundError:
        from PySide2.QtGui import QColor, QPalette

    palette = theme._build_dark_palette()
    assert palette.color(QPalette.Active, QPalette.Window) == QColor(53, 53, 53)
    assert palette.color(QPalette.Active, QPalette.WindowText) == QColor(255, 255, 255)
    assert palette.color(QPalette.Active, QPalette.Base) == QColor(42, 42, 42)
    assert palette.color(QPalette.Active, QPalette.Highlight) == QColor(42, 130, 218)
    assert palette.color(QPalette.Disabled, QPalette.Text) == QColor(127, 127, 127)


def test_detect_system_theme_returns_known_value():
    result = theme.detect_system_theme()
    assert result in {theme.THEME_LIGHT, theme.THEME_DARK}


def test_detect_system_theme_uses_qt_colorscheme_when_available(monkeypatch):
    try:
        from PySide6.QtCore import Qt
    except ModuleNotFoundError:
        from PySide2.QtCore import Qt

    if not hasattr(Qt, "ColorScheme"):
        pytest.skip("Qt.ColorScheme not available on this Qt version")

    class FakeStyleHints:
        def colorScheme(self):
            return Qt.ColorScheme.Dark

    class FakeApp:
        @staticmethod
        def styleHints():
            return FakeStyleHints()

    monkeypatch.setattr(theme, "QGuiApplication", FakeApp)
    assert theme.detect_system_theme() == theme.THEME_DARK


@pytest.mark.skipif(sys.platform != "win32", reason="Windows registry only")
def test_detect_system_theme_windows_registry_light(monkeypatch):
    import winreg

    monkeypatch.setattr(theme, "QGuiApplication", None)

    class FakeKey:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_open(*_args, **_kwargs):
        return FakeKey()

    def fake_query(_key, _name):
        return (1, winreg.REG_DWORD)

    monkeypatch.setattr(winreg, "OpenKey", fake_open)
    monkeypatch.setattr(winreg, "QueryValueEx", fake_query)
    assert theme.detect_system_theme() == theme.THEME_LIGHT


def test_detect_system_theme_swallows_exceptions(monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(theme, "_detect_from_qt", boom)
    monkeypatch.setattr(theme, "_detect_from_os", boom)
    assert theme.detect_system_theme() == theme.THEME_LIGHT


class _FakeApp:
    def __init__(self):
        self.style_arg = "<unset>"
        self.style_sheet = "<unset>"
        self.palette_arg = None

    def setStyle(self, style):
        self.style_arg = style

    def setStyleSheet(self, sheet):
        self.style_sheet = sheet

    def setPalette(self, palette):
        self.palette_arg = palette


def test_apply_theme_light_uses_fusion_and_default_palette(monkeypatch):
    app = _FakeApp()
    theme.apply_theme(app, theme.THEME_LIGHT)
    assert app.style_arg is not None
    assert app.style_sheet == ""
    try:
        from PySide6.QtGui import QPalette
    except ModuleNotFoundError:
        from PySide2.QtGui import QPalette
    assert isinstance(app.palette_arg, QPalette)


def test_apply_theme_dark_applies_dark_window_color():
    try:
        from PySide6.QtGui import QColor, QPalette
    except ModuleNotFoundError:
        from PySide2.QtGui import QColor, QPalette

    app = _FakeApp()
    theme.apply_theme(app, theme.THEME_DARK)
    assert app.palette_arg.color(QPalette.Active, QPalette.Window) == QColor(53, 53, 53)


def test_apply_theme_system_resolves_through_detector(monkeypatch):
    monkeypatch.setattr(theme, "detect_system_theme", lambda: theme.THEME_DARK)
    app = _FakeApp()
    theme.apply_theme(app, theme.THEME_SYSTEM)
    try:
        from PySide6.QtGui import QColor, QPalette
    except ModuleNotFoundError:
        from PySide2.QtGui import QColor, QPalette
    assert app.palette_arg.color(QPalette.Active, QPalette.Window) == QColor(53, 53, 53)


def test_apply_theme_invalid_value_falls_back_to_system(monkeypatch):
    monkeypatch.setattr(theme, "detect_system_theme", lambda: theme.THEME_LIGHT)
    app = _FakeApp()
    theme.apply_theme(app, "garbage")
    try:
        from PySide6.QtGui import QPalette
    except ModuleNotFoundError:
        from PySide2.QtGui import QPalette
    assert isinstance(app.palette_arg, QPalette)


def test_apply_theme_handles_none_app():
    theme.apply_theme(None, theme.THEME_LIGHT)
