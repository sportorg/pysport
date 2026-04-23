import atexit
import logging.config
import os
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Dict, Tuple

try:
    from importlib.resources import as_file, files
except ImportError:
    from importlib_resources import as_file, files

NAME = "SportOrg"
VERSION = "v1.8.0b1"
PYTHON_VERSION = (
    f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
)

ENV_PREFIX = "SPORTORG_"
DEBUG = os.getenv(f"{ENV_PREFIX}DEBUG", "false").lower() in ["1", "yes", "true"]
TEMPLATES_PATH = os.getenv(f"{ENV_PREFIX}TEMPLATES_PATH", "")


def is_executable() -> bool:
    return hasattr(sys, "frozen")


def module_path() -> str:
    if is_executable():
        return os.path.dirname(sys.executable)

    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


BASE_DIR = module_path()


def base_dir(*paths) -> str:
    return os.path.join(BASE_DIR, *paths)


def runtime_dir(*paths) -> str:
    return os.path.join(os.path.abspath(os.getcwd()), *paths)


_RESOURCE_STACK = ExitStack()
atexit.register(_RESOURCE_STACK.close)
_RESOURCE_PATH_CACHE: Dict[Tuple[str, ...], str] = {}
_RESOURCE_ROOT = files("sportorg.data")


def package_data_path(*paths) -> str:
    key = tuple(paths)
    if key not in _RESOURCE_PATH_CACHE:
        resource = _RESOURCE_ROOT.joinpath(*paths)
        _RESOURCE_PATH_CACHE[key] = str(
            _RESOURCE_STACK.enter_context(as_file(resource))
        )

    return _RESOURCE_PATH_CACHE[key]


IMG_DIR = package_data_path("img")


def img_dir(*paths) -> str:
    return os.path.join(IMG_DIR, *paths)


ICON_DIR = img_dir("icon")


def icon_dir(*paths) -> str:
    return os.path.join(ICON_DIR, *paths)


LOG_DIR = runtime_dir("logs")


def log_dir(*paths) -> str:
    return os.path.join(LOG_DIR, *paths)


DATA_DIR = runtime_dir("data")


def data_dir(*paths) -> str:
    return os.path.join(DATA_DIR, *paths)


CONFIGS_DIR = runtime_dir("configs")


def configs_dir(*paths) -> str:
    return os.path.join(CONFIGS_DIR, *paths)


DEFAULT_TEMPLATE_DIR = package_data_path("templates")
TEMPLATE_DIR = TEMPLATES_PATH or DEFAULT_TEMPLATE_DIR


SOUND_DIR = package_data_path("sounds")


def sound_dir(*paths) -> str:
    return os.path.join(SOUND_DIR, *paths)


STYLE_DIR = package_data_path("styles")


def style_dir(*paths) -> str:
    return os.path.join(STYLE_DIR, *paths)


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


def locale_dir(*paths) -> str:
    return os.path.join(LOCALE_DIR, *paths)


DIRS = [
    DATA_DIR,
    CONFIGS_DIR,
    LOG_DIR,
]

if TEMPLATES_PATH:
    DIRS.append(TEMPLATE_DIR)

for _DIR in DIRS:
    os.makedirs(_DIR, exist_ok=True)

LOG_CONFIG = {
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

logging.config.dictConfig(LOG_CONFIG)


def get_creator_name() -> str:
    return f"{NAME} {VERSION}"
