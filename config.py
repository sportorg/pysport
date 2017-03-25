import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.join(BASE_DIR, 'sportorg')
# BASE_DIR = os.getcwd()
# BASE_DIR = 'C:\\Users\\Danil\\PycharmProjects\\sportorg'
NAME = 'SportOrg'
AUTHOR = 'Akhtarov Danil'
__version__ = '1.0.0'

DATA_DIR = os.path.join(BASE_DIR, 'data')
CONFIG_INI = os.path.join(DATA_DIR, 'config.ini')

IMG_DIR = os.path.join(BASE_DIR, 'img')
ICON_DIR = os.path.join(IMG_DIR, 'icon')
ICON = os.path.join(ICON_DIR, 'sportorg.ico')

LOCALE_DIR = os.path.join(BASE_DIR, 'languages')
