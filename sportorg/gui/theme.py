import logging
import subprocess
import sys
from typing import Optional

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QGuiApplication, QPalette
    from PySide6.QtWidgets import QApplication, QStyleFactory
except ModuleNotFoundError:
    from PySide2.QtCore import Qt
    from PySide2.QtGui import QColor, QGuiApplication, QPalette
    from PySide2.QtWidgets import QApplication, QStyleFactory

THEME_SYSTEM = "system"
THEME_LIGHT = "light"
THEME_DARK = "dark"
VALID_THEMES = {THEME_SYSTEM, THEME_LIGHT, THEME_DARK}

_LOGGER = logging.getLogger(__name__)


def _build_light_palette() -> QPalette:
    # On Qt 6.5+ Windows 11 with dark OS theme, both QPalette() and
    # QStyle.standardPalette() return the OS-adapted dark palette. The only
    # deterministic way to render light regardless of OS color scheme is to
    # set every role explicitly, mirroring _build_dark_palette below.
    palette = QPalette()

    palette.setColor(QPalette.Window, QColor(239, 239, 239))
    palette.setColor(QPalette.WindowText, Qt.black)
    palette.setColor(QPalette.Base, Qt.white)
    palette.setColor(QPalette.AlternateBase, QColor(247, 247, 247))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ToolTipText, Qt.black)
    palette.setColor(QPalette.Text, Qt.black)
    palette.setColor(QPalette.Button, QColor(239, 239, 239))
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(QPalette.BrightText, Qt.white)
    palette.setColor(QPalette.Link, Qt.blue)
    palette.setColor(QPalette.Highlight, QColor(48, 140, 198))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    palette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))

    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(190, 190, 190))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(190, 190, 190))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(190, 190, 190))
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(190, 190, 190))

    return palette


def _build_dark_palette() -> QPalette:
    palette = QPalette()

    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(42, 42, 42))
    palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    palette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))

    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))

    return palette


def _detect_from_qt() -> Optional[str]:
    if QGuiApplication is None:
        return None
    if not hasattr(Qt, "ColorScheme"):
        return None

    hints = (
        QGuiApplication.styleHints() if hasattr(QGuiApplication, "styleHints") else None
    )
    if hints is None or not hasattr(hints, "colorScheme"):
        return None

    scheme = hints.colorScheme()
    if scheme == Qt.ColorScheme.Dark:
        return THEME_DARK
    if scheme == Qt.ColorScheme.Light:
        return THEME_LIGHT
    return None


def _detect_from_os() -> Optional[str]:
    if sys.platform == "win32":
        return _detect_from_windows_registry()
    if sys.platform == "darwin":
        return _detect_from_macos_defaults()
    if sys.platform.startswith("linux"):
        return _detect_from_linux_gsettings()
    return None


def _detect_from_windows_registry() -> Optional[str]:
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
    return THEME_LIGHT if int(value) == 1 else THEME_DARK


def _detect_from_macos_defaults() -> Optional[str]:
    result = subprocess.run(
        ["defaults", "read", "-g", "AppleInterfaceStyle"],
        capture_output=True,
        text=True,
        timeout=2,
    )
    if result.returncode != 0:
        return THEME_LIGHT
    return THEME_DARK if "Dark" in result.stdout else THEME_LIGHT


def _detect_from_linux_gsettings() -> Optional[str]:
    result = subprocess.run(
        ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
        capture_output=True,
        text=True,
        timeout=2,
    )
    if result.returncode != 0:
        return None
    return THEME_DARK if "dark" in result.stdout.lower() else THEME_LIGHT


def detect_system_theme() -> str:
    try:
        qt_result = _detect_from_qt()
        if qt_result is not None:
            return qt_result
    except Exception as exc:
        _LOGGER.debug("Qt color scheme detection failed: %s", exc)

    try:
        os_result = _detect_from_os()
        if os_result is not None:
            return os_result
    except Exception as exc:
        _LOGGER.debug("OS theme detection failed: %s", exc)

    return THEME_LIGHT


def apply_theme(app: Optional[QApplication], choice: str) -> None:
    if app is None:
        return

    if choice not in VALID_THEMES:
        choice = THEME_SYSTEM

    resolved = detect_system_theme() if choice == THEME_SYSTEM else choice

    fusion = QStyleFactory.create("Fusion")
    if fusion is not None:
        app.setStyle(fusion)
    else:
        _LOGGER.debug("Fusion style unavailable on this Qt build")

    app.setStyleSheet("")

    palette = (
        _build_dark_palette() if resolved == THEME_DARK else _build_light_palette()
    )
    app.setPalette(palette)

    # On Qt 6.8+, force the colorScheme so Qt's platform theme stops applying
    # the OS palette on top of ours. No-op on older Qt / PySide2.
    _force_color_scheme(resolved)


def _force_color_scheme(resolved: str) -> None:
    if not hasattr(Qt, "ColorScheme"):
        return
    if QGuiApplication is None or not hasattr(QGuiApplication, "styleHints"):
        return

    hints = QGuiApplication.styleHints()
    if hints is None or not hasattr(hints, "setColorScheme"):
        return

    target = Qt.ColorScheme.Dark if resolved == THEME_DARK else Qt.ColorScheme.Light
    try:
        hints.setColorScheme(target)
    except Exception as exc:
        _LOGGER.debug("setColorScheme failed: %s", exc)
