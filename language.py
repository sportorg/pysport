import configparser
import gettext
import os
import config

conf = configparser.ConfigParser()
conf.read(config.CONFIG_INI)
locale_current = conf.get('locale', 'current', fallback='ru_RU')

cat = gettext.Catalog(config.NAME.lower(), config.LOCALE_DIR, languages=[locale_current])
_ = cat.gettext


def get_languages():
    dirs = os.listdir(path=config.LOCALE_DIR)
    return dirs
