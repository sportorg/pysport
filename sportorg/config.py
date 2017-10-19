import os
import sys

NAME = 'SportOrg'
VERSION = '0.7.2-beta'
DEBUG = True


def module_path():
    if hasattr(sys, "frozen"):
        return os.path.dirname(
            sys.executable
        )

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


PLUGIN_DIR = base_dir('sportorg', 'app', 'plugins')


def plugin_dir(*paths):
    return os.path.join(PLUGIN_DIR, *paths)


TEMPLATE_DIR = base_dir('templates')


def template_dir(*paths):
    return os.path.join(TEMPLATE_DIR, *paths)


ICON = icon_dir('sportorg.ico')

CONFIG_INI = data_dir('config.ini')

LOCALE_DIR = base_dir('languages')

LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(levelname)s %(asctime)-15s %(processName)-10s@%(filename)s:%(lineno)d %(message)s'
        },
        'cls': {
            'class': 'logging.Formatter',
            'format': '%(levelname)s %(processName)-10s@%(filename)s:%(lineno)d %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'cls'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': log_dir(NAME.lower() + '.log'),
            'mode': 'a',
            'formatter': 'detailed'
        },
        'errors': {
            'class': 'logging.FileHandler',
            'filename': log_dir(NAME.lower() + '-errors.log'),
            'mode': 'a',
            'level': 'ERROR',
            'formatter': 'detailed'
        },
    },
    'loggers': {
        'main': {
            'handlers': ['file']
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file', 'errors']
    },
}

DIRS = [
    IMG_DIR,
    ICON_DIR,
    DATA_DIR,
    LOCALE_DIR,
    LOG_DIR,
    TEMPLATE_DIR
]

for DIR in DIRS:
    if not os.path.exists(DIR):
        os.makedirs(DIR)
