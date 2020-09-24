import logging.config
import os
import sys

from pydantic import BaseSettings

from sportorg.common.version import Version


class Env(BaseSettings):
    DEBUG: bool = False

    class Config:
        env_file = '.env'


NAME = 'SportOrg'
VERSION = Version(1, 5, 0, 0, 'v')


def is_executable():
    return hasattr(sys, 'frozen')


def module_path():
    if is_executable():
        return os.path.dirname(sys.executable)

    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


BASE_DIR = module_path()


def base_dir(*paths):
    return os.path.join(BASE_DIR, *paths)


IMG_DIR = base_dir('img')


def img_dir(*paths):
    return os.path.join(IMG_DIR, *paths)


ICON_DIR = img_dir('icon')


def icon_dir(*paths):
    return os.path.join(ICON_DIR, *paths)


LOG_DIR = base_dir('log')


def log_dir(*paths):
    return os.path.join(LOG_DIR, *paths)


DATA_DIR = base_dir('data')


def data_dir(*paths):
    return os.path.join(DATA_DIR, *paths)


TEMPLATE_DIR = base_dir('templates')


def template_dir(*paths):
    return os.path.join(TEMPLATE_DIR, *paths)


SOUND_DIR = base_dir('sounds')


def sound_dir(*paths):
    return os.path.join(SOUND_DIR, *paths)


SCRIPT_DIR = base_dir('scripts')


def script_dir(*paths):
    return os.path.join(SCRIPT_DIR, *paths)


STYLE_DIR = base_dir('styles')


def style_dir(*paths):
    return os.path.join(STYLE_DIR, *paths)


env = Env(_env_file=base_dir('.env'))
DEBUG = env.DEBUG

ICON = icon_dir('sportorg.svg')

CONFIG_INI = data_dir('config.ini')

LOCALE_DIR = base_dir('languages')

NAMES_FILE = base_dir('configs', 'names.txt')

REGIONS_FILE = base_dir('configs', 'regions.txt')

STATUS_COMMENTS_FILE = base_dir('configs', 'status_comments.txt')

RANKING_SCORE_FILE = base_dir('configs', 'ranking.txt')

DIRS = [
    IMG_DIR,
    ICON_DIR,
    DATA_DIR,
    LOCALE_DIR,
    LOG_DIR,
    TEMPLATE_DIR,
    SOUND_DIR,
    SCRIPT_DIR,
    STYLE_DIR,
]

for _DIR in DIRS:
    if not os.path.exists(_DIR):
        os.makedirs(_DIR)

LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(levelname)s %(asctime)-15s %(threadName)s@%(filename)s:%(lineno)d %(message)s',
        },
        'cls': {
            'class': 'logging.Formatter',
            'format': '%(levelname)s %(threadName)s@%(filename)s:%(lineno)d %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': logging.DEBUG,
            'formatter': 'cls',
            'stream': sys.stdout,
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': log_dir(NAME.lower() + '.log'),
            'mode': 'a',
            'formatter': 'detailed',
        },
        'errors': {
            'class': 'logging.FileHandler',
            'filename': log_dir(NAME.lower() + '-errors.log'),
            'mode': 'a',
            'level': logging.ERROR,
            'formatter': 'detailed',
        },
    },
    'loggers': {'main': {'handlers': ['file']}},
    'root': {'level': logging.DEBUG, 'handlers': ['console', 'file', 'errors']},
}

logging.config.dictConfig(LOG_CONFIG)
