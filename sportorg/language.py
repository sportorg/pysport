import configparser
import gettext
import logging
import os
from typing import Callable, List

from sportorg import config

logger = logging.getLogger(__name__)


def _get_conf_locale() -> str:
    conf = configparser.ConfigParser()
    try:
        conf.read(config.CONFIG_INI)
    except Exception as e:
        logger.exception(e)
        # remove incorrect config
        os.remove(config.CONFIG_INI)
    return conf.get('locale', 'current', fallback='ru_RU')


locale_current = _get_conf_locale()


def generate_mo() -> None:
    import polib

    name = config.NAME.lower()
    path = config.base_dir(config.LOCALE_DIR, locale_current, 'LC_MESSAGES', name)
    try:
        po = polib.pofile(path + '.po')
        po.save_as_mofile(path + '.mo')
    except Exception as e:
        logger.error(str(e))


def locale() -> Callable[[str], str]:
    cat = gettext.Catalog(
        config.NAME.lower(), config.LOCALE_DIR, languages=[locale_current]
    )

    def get_text(message: str) -> str:
        return cat.gettext(message)

    return get_text


def get_languages() -> List[str]:
    return os.listdir(path=config.LOCALE_DIR)


translate = locale()


if __name__ == '__main__':
    logger.info('Generate mo files')
    generate_mo()
