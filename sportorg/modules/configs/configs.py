import configparser
import logging
import os

from sportorg import config as sportorg_config
from sportorg.common.singleton import Singleton


class ConfigFile(object):
    GEOMETRY = 'geometry'
    CONFIGURATION = 'configuration'
    LOCALE = 'locale'
    DIRECTORY = 'directory'
    PATH = 'path'
    SOUND = 'sound'
    PRINTER = 'printer'
    RANKING = 'ranking'


class Parser:
    @staticmethod
    def is_bool(val):
        return val in ['True', 'False', '0', '1', True, False, 0, 1, 'true', 'false']

    @staticmethod
    def is_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_float(s):
        try:
            float(s)
            return True
        except ValueError:
            return False


class Configurations:
    def __init__(self, configurations=None):
        if configurations is None:
            configurations = {}
        self._configurations = configurations

    def set(self, config, value):
        self._configurations[config] = value

    def get(self, config, nvl_value=None):
        if config in self._configurations:
            return self._configurations[config]
        else:
            return nvl_value

    def get_all(self):
        return self._configurations

    def set_parse(self, option, param):
        if Parser.is_bool(param):
            param = param in ['True', '1', True, 1, 'true']
        elif Parser.is_int(param):
            param = int(param)
        elif Parser.is_float(param):
            param = float(param)
        self.set(option, param)


class Config(metaclass=Singleton):
    def __init__(self):
        self._config_parser = configparser.ConfigParser()
        self._configurations = {
            ConfigFile.CONFIGURATION: Configurations(
                {
                    'current_locale': 'ru_RU',
                    'autoconnect': False,
                    'open_recent_file': False,
                    'use_birthday': False,
                    'check_updates': True,
                    'autosave_interval': 0,
                }
            ),
            ConfigFile.SOUND: Configurations(
                {
                    'enabled': False,
                    'successful': '',
                    'unsuccessful': '',
                }
            ),
            ConfigFile.PRINTER: Configurations(
                {
                    'main': '',
                    'split': '',
                }
            ),
            ConfigFile.RANKING: Configurations(
                {
                    'not_qualified': 0,
                    'iii_y': 1,
                    'ii_y': 2,
                    'i_y': 3,
                    'iii': 6,
                    'ii': 25,
                    'i': 50,
                    'kms': 80,
                    'ms': 100,
                    'msmk': 100,
                    'zms': 100,
                    'start_limit': 10,
                    'finish_limit': 5,
                    'start_limit_relay': 6,
                    'finish_limit_relay': 4,
                    'sum_count': 10,
                    'sum_count_relay': 10,
                    'relay_ranking_method': 'personal',  # also use 'average' to get average
                }
            ),
        }

    @property
    def parser(self):
        return self._config_parser

    @property
    def configuration(self):
        return self._configurations[ConfigFile.CONFIGURATION]

    @property
    def sound(self):
        return self._configurations[ConfigFile.SOUND]

    @property
    def printer(self):
        return self._configurations[ConfigFile.PRINTER]

    @property
    def ranking(self):
        return self._configurations[ConfigFile.RANKING]

    def read(self):
        self.parser.read(sportorg_config.CONFIG_INI)

        try:
            for config_name in self._configurations.keys():
                if self.parser.has_section(config_name):
                    for option in self.parser.options(config_name):
                        self._configurations[config_name].set_parse(
                            option,
                            self.parser.get(
                                config_name,
                                option,
                                fallback=self._configurations[config_name].get(option),
                            ),
                        )

            self.configuration.set(
                'current_locale',
                self.parser.get(ConfigFile.LOCALE, 'current', fallback='ru_RU'),
            )
        except Exception as e:
            logging.exception(e)
            # remove incorrect config
            if config_name:
                os.remove(config_name)

    def save(self):
        for config_name in self._configurations.keys():
            self.parser[config_name] = self._configurations[config_name].get_all()

        self.parser[ConfigFile.LOCALE] = {
            'current': self.configuration.get('current_locale')
        }

        with open(sportorg_config.CONFIG_INI, 'w') as configfile:
            self.parser.write(configfile)
