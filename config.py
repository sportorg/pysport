import os
import sys


def module_path():
    if hasattr(sys, "frozen"):
        return os.path.dirname(
            sys.executable
        )
    return os.path.dirname(__file__)


BASE_DIR = module_path()

NAME = 'SportOrg'
AUTHOR = 'Akhtarov Danil'
__version__ = '1.0.0'

DATA_DIR = os.path.join(BASE_DIR, 'data')
CONFIG_INI = os.path.join(DATA_DIR, 'config.ini')

IMG_DIR = os.path.join(BASE_DIR, 'img')
ICON_DIR = os.path.join(IMG_DIR, 'icon')
ICON = os.path.join(ICON_DIR, 'sportorg.ico')

LOCALE_DIR = os.path.join(BASE_DIR, 'languages')


def base_dir(paths):
    return os.path.join(BASE_DIR, paths)


def img_dir(paths):
    return os.path.join(IMG_DIR, paths)


def icon_dir(paths):
    return os.path.join(ICON_DIR, paths)
