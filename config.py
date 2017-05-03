import os
import sys

import time

NAME = 'SportOrg'
AUTHOR = 'Akhtarov Danil'
__version__ = '1.0.0'
DEBUG = True


def module_path():
    if hasattr(sys, "frozen"):
        return os.path.dirname(
            sys.executable
        )
    return os.path.dirname(__file__)


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


ICON = icon_dir('sportorg.ico')

CONFIG_INI = data_dir('config.ini')

LOCALE_DIR = base_dir('languages')

FORMAT = '%(asctime)-15s - %(filename)s - %(levelname)s - %(message)s'

LOG_CONFIG = dict(filename=log_dir(NAME.lower() + str(time.strftime("%Y%m%d")) + '.log'), format=FORMAT)
