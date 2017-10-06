import configparser
import gettext
import logging
import os
from sportorg import config

conf = configparser.ConfigParser()
conf.read(config.CONFIG_INI)
locale_current = conf.get('locale', 'current', fallback='ru_RU')


def locale():
    cat = gettext.Catalog(config.NAME.lower(), config.LOCALE_DIR, languages=[locale_current])

    def get_text(message):
        result = cat.gettext(message)
        if result == message:
            logging.debug('No translation "{}"'.format(result))
        return result

    return get_text


def get_languages():
    dirs = os.listdir(path=config.LOCALE_DIR)
    return dirs


_ = locale()
