import logging
import sys
from multiprocessing import freeze_support

try:
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError:
    from PySide2.QtWidgets import QApplication

from sportorg import config
from sportorg.common.singleton import Singleton
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.main_window import MainWindow
from sportorg.language import generate_mo
from sportorg.models.constant import (
    PersonNames,
    RankingTable,
    Regions,
    RentCards,
    StatusComments,
    PersonMiddleNames,
)


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
        self.set_status_comments()
        self.set_names()
        self.set_middle_names()
        self.set_regions()
        self.set_ranking()
        self.set_rent_cards()
        self.main_window.show_window()
        sys.exit(self.app.exec_())

    @staticmethod
    def set_status_comments():
        try:
            with open(config.STATUS_COMMENTS_FILE, encoding="utf-8") as f:
                content = f.readlines()
            StatusComments().set([x.strip() for x in content])

            with open(config.STATUS_DEFAULT_COMMENTS_FILE, encoding="utf-8") as f:
                content = f.readlines()
            StatusComments().set_default_statuses(content)
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_names():
        try:
            with open(config.NAMES_FILE, encoding="utf-8") as f:
                content = f.readlines()
            PersonNames().set([x.strip() for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_middle_names():
        try:
            with open(config.MIDDLE_NAMES_FILE, encoding="utf-8") as f:
                content = f.readlines()
            PersonMiddleNames().set([x.strip() for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_regions():
        try:
            with open(config.REGIONS_FILE, encoding="utf-8") as f:
                content = f.readlines()
            Regions().set([x.strip() for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_ranking():
        try:
            with open(config.RANKING_SCORE_FILE, encoding="utf-8") as f:
                content = f.readlines()
            RankingTable().set([x.strip().split(";") for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_rent_cards():
        try:
            with open(config.data_dir("rent_cards.txt"), encoding="utf-8") as f:
                content = f.read()
            RentCards().set_from_text(content)
        except FileNotFoundError:
            pass
        except Exception as e:
            logging.exception(str(e))
