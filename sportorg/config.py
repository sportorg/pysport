import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

from sportorg import paths

NAME = "SportOrg"
VERSION = "v1.8.0b2"
PYTHON_VERSION = (
    f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
)

ENV_PREFIX = "SPORTORG_"
DEBUG = os.getenv(f"{ENV_PREFIX}DEBUG", "false").lower() in ["1", "yes", "true"]
TEMPLATES_PATH = os.getenv(f"{ENV_PREFIX}TEMPLATES_PATH", "")


def is_executable() -> bool:
    return paths.is_executable()


def module_path() -> str:
    return paths.app_dir()


BASE_DIR = paths.app_dir()


def base_dir(*parts) -> str:
    return paths.app_dir(*parts)


def package_data_path(*parts) -> str:
    return paths.package_dir(*parts)


IMG_DIR = package_data_path("img")


def img_dir(*parts) -> str:
    return os.path.join(IMG_DIR, *parts)


ICON_DIR = img_dir("icon")


def icon_dir(*parts) -> str:
    return os.path.join(ICON_DIR, *parts)


LOG_DIR = paths.log_dir()


def log_dir(*parts) -> str:
    return paths.log_dir(*parts)


DATA_DIR = paths.data_dir()


def data_dir(*parts) -> str:
    return paths.data_dir(*parts)


def sound_dir(*parts) -> str:
    """Sounds resolve through ``data/sounds`` and fall back to the package."""
    return paths.resolve_seeded("sounds", *parts)


STYLE_DIR = package_data_path("styles")


def style_dir(*parts) -> str:
    return os.path.join(STYLE_DIR, *parts)


COMMIT_VERSION_FILE = base_dir("version")


def commit_version() -> str:
    path = Path(COMMIT_VERSION_FILE)
    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8")


ICON = icon_dir("sportorg.svg")

CONFIG_INI = data_dir("config.ini")
SETTINGS_JSON = data_dir("settings.json")

LOCALE_DIR = package_data_path("languages")


def locale_dir(*parts) -> str:
    return os.path.join(LOCALE_DIR, *parts)


def build_log_config() -> Dict[str, Any]:
    """Build the logging configuration.

    Built on demand rather than at import time: the file handlers name paths
    inside ``logs/``, which only exists once :func:`sportorg.startup.init` has
    created it.
    """
    return {
        "version": 1,
        "formatters": {
            "detailed": {
                "class": "logging.Formatter",
                "format": "%(levelname)s %(asctime)-15s %(threadName)s@%(filename)s:%(lineno)d %(message)s",
            },
            "cls": {
                "class": "logging.Formatter",
                "format": "%(levelname)s %(threadName)s@%(filename)s:%(lineno)d %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": logging.DEBUG,
                "formatter": "cls",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": log_dir(NAME.lower() + ".log"),
                "mode": "a",
                "formatter": "detailed",
            },
            "errors": {
                "class": "logging.FileHandler",
                "filename": log_dir(NAME.lower() + "-errors.log"),
                "mode": "a",
                "level": logging.ERROR,
                "formatter": "detailed",
            },
        },
        "loggers": {"main": {"handlers": ["file"]}},
        "root": {"level": logging.DEBUG, "handlers": ["console", "file", "errors"]},
    }


def get_creator_name() -> str:
    return f"{NAME} {VERSION}"
