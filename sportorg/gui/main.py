import logging
import sys
from multiprocessing import freeze_support

try:
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError:
    from PySide2.QtWidgets import QApplication

from sportorg import config, settings
from sportorg.common.singleton import Singleton
from sportorg.gui import theme
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.main_window import MainWindow
from sportorg.language import generate_mo
from sportorg.models.constant import (
    Countries,
    Groups,
    PersonMiddleNames,
    PersonNames,
    RankingTable,
    Regions,
    RentCards,
    StatusComments,
)
from sportorg.rust_example import log_rust_status


class Application(metaclass=Singleton):
    def __init__(self):
        self.argv = sys.argv
        self.app = QApplication(self.argv)
        self.main_window = MainWindow(self.argv)
        GlobalAccess().set_app(self)

    def get_main_window(self):
        return self.main_window

    def run(self):
        if config.DEBUG:
            generate_mo()
        freeze_support()
        log_rust_status()
        try:
            settings.load_settings_on_startup()
        except Exception as e:
            logging.exception("Error loading settings: %s", str(e))
        theme.apply_theme(self.app, settings.SETTINGS.theme)
        self.set_status_comments()
        self.set_countries()
        self.set_groups()
        self.set_names()
        self.set_middle_names()
        self.set_regions()
        self.set_ranking()
        self.set_ranking_ardf()
        self.set_rent_cards()
        self.main_window.show_window()
        sys.exit(self.app.exec_())

    @staticmethod
    def set_status_comments():
        try:
            with open(settings.status_comments_path(), encoding="utf-8") as f:
                content = f.readlines()
            StatusComments().set([x.strip() for x in content])

        except Exception as e:
            logging.exception(str(e))

        try:
            with open(settings.status_default_comments_path(), encoding="utf-8") as f:
                content = f.readlines()
            StatusComments().set_default_statuses(content)
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_countries():
        try:
            with open(settings.countries_path(), encoding="utf-8") as f:
                content = f.readlines()
            Countries().set([x.strip() for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_groups():
        try:
            with open(settings.groups_path(), encoding="utf-8") as f:
                content = f.readlines()
            Groups().set([x.strip() for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_names():
        try:
            with open(settings.names_path(), encoding="utf-8") as f:
                content = f.readlines()
            PersonNames().set([x.strip() for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_middle_names():
        try:
            with open(settings.middle_names_path(), encoding="utf-8") as f:
                content = f.readlines()
            PersonMiddleNames().set([x.strip() for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_regions():
        try:
            with open(settings.regions_path(), encoding="utf-8") as f:
                content = f.readlines()
            Regions().set([x.strip() for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_ranking():
        try:
            with open(settings.ranking_score_path(), encoding="utf-8") as f:
                content = f.readlines()
            RankingTable().set_table([x.strip().split(";") for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_ranking_ardf():
        try:
            with open(settings.ranking_ardf_score_path(), encoding="utf-8") as f:
                content = f.readlines()
            RankingTable().set_table([x.strip().split(";") for x in content], "ardf")
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_rent_cards():
        try:
            with open(settings.rent_cards_path(), encoding="utf-8") as f:
                content = f.read()
            RentCards().set_from_text(content)
        except FileNotFoundError:
            pass
        except Exception as e:
            logging.exception(str(e))
