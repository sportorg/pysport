import unittest

import polib

from sportorg import config
from sportorg.language import get_languages


class TestLang(unittest.TestCase):

    def setUp(self):
        print('=========>', self.__class__.__name__, self._testMethodName)

    def test_duplicates(self):
        locales = get_languages()
        name = config.NAME.lower()
        for locale in locales:
            path = config.base_dir(config.LOCALE_DIR, locale, 'LC_MESSAGES', name)
            po = polib.pofile(path + '.po', check_for_duplicates=True)
            po.save_as_mofile(path + '.mo')
