import logging.config
import os
import sys
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings


class Env(BaseSettings):
    DEBUG: bool = False
    TEMPLATES_PATH: Optional[str]

    class Config:
        env_file = ".env"


NAME = "SportOrg"
VERSION = "v1.7.1"


def is_executable() -> bool:
    return hasattr(sys, "frozen")


def module_path() -> str:
    if is_executable():
        return os.path.dirname(sys.executable)

    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


BASE_DIR = module_path()


def base_dir(*paths) -> str:
    return os.path.join(BASE_DIR, *paths)


env = Env(_env_file=base_dir(".env"))  # type:ignore
DEBUG = env.DEBUG
IMG_DIR = base_dir("img")


def img_dir(*paths) -> str:
    return os.path.join(IMG_DIR, *paths)


ICON_DIR = img_dir("icon")


def icon_dir(*paths) -> str:
    return os.path.join(ICON_DIR, *paths)


LOG_DIR = base_dir("log")


def log_dir(*paths) -> str:
    return os.path.join(LOG_DIR, *paths)


DATA_DIR = base_dir("data")


def data_dir(*paths) -> str:
    return os.path.join(DATA_DIR, *paths)


TEMPLATE_DIR = env.TEMPLATES_PATH or base_dir("templates")


def set_template_dir(dirpath: str) -> None:
    global TEMPLATE_DIR
    TEMPLATE_DIR = dirpath


def template_dir(*paths) -> str:
    return os.path.join(TEMPLATE_DIR, *paths)


SOUND_DIR = base_dir("sounds")


def sound_dir(*paths) -> str:
    return os.path.join(SOUND_DIR, *paths)


STYLE_DIR = base_dir("styles")


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

LOCALE_DIR = base_dir("languages")

NAMES_FILE = base_dir("configs", "names.txt")

REGIONS_FILE = base_dir("configs", "regions.txt")

STATUS_COMMENTS_FILE = base_dir("configs", "status_comments.txt")

STATUS_DEFAULT_COMMENTS_FILE = base_dir("configs", "status_default.txt")

RANKING_SCORE_FILE = base_dir("configs", "ranking.txt")

DIRS = [
    IMG_DIR,
    ICON_DIR,
    DATA_DIR,
    LOCALE_DIR,
    LOG_DIR,
    TEMPLATE_DIR,
    SOUND_DIR,
    STYLE_DIR,
]

for _DIR in DIRS:
    if not os.path.exists(_DIR):
        os.makedirs(_DIR)

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
