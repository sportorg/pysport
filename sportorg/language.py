import configparser
import gettext
import logging
import os

from sportorg import config


def _get_conf_locale():
    conf = configparser.ConfigParser()
    try:
        conf.read(config.CONFIG_INI)
    except Exception as e:
        logging.exception(e)
        # remove incorrect config
        os.remove(config.CONFIG_INI)
    return conf.get('locale', 'current', fallback='ru_RU')


locale_current = _get_conf_locale()


if config.DEBUG:
    import polib

    def _generate():
        name = config.NAME.lower()
        path = config.base_dir(config.LOCALE_DIR, locale_current, 'LC_MESSAGES', name)
        try:
            po = polib.pofile(path + '.po')
            po.save_as_mofile(path + '.mo')
        except Exception as e:
            logging.error(str(e))

    _generate()


def locale():
    cat = gettext.Catalog(
        config.NAME.lower(), config.LOCALE_DIR, languages=[locale_current]
    )

    def get_text(message):
        result = cat.gettext(message)
        # if result == message:
        #     logging.debug('No translation "{}"'.format(result))
        return result

    return get_text


def get_languages():
    dirs = os.listdir(path=config.LOCALE_DIR)
    return dirs


translate = locale()
