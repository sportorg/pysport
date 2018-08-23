from multiprocessing import freeze_support

import sys
from PyQt5.QtWidgets import QApplication

from sportorg import config
from sportorg.core.singleton import Singleton
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.main_window import MainWindow
from sportorg.models.constant import StatusComments, PersonNames, Regions, RankingTable


class Application(metaclass=Singleton):
    def __init__(self):
        self.argv = sys.argv
        self.app = QApplication(self.argv)
        self.main_window = MainWindow(self.argv)
        GlobalAccess().set_app(self)

    def get_main_window(self):
        return self.main_window

    def run(self):
        freeze_support()
        self.set_status_comments()
        self.set_names()
        self.set_regions()
        self.set_ranking()
        self.main_window.show_window()
        sys.exit(self.app.exec())

    @staticmethod
    def set_status_comments():
        try:
            with open(config.STATUS_COMMENTS_FILE, encoding='utf-8') as f:
                content = f.readlines()
            StatusComments().set([x.strip() for x in content])
        except Exception as e:
            print(str(e))

    @staticmethod
    def set_names():
        try:
            with open(config.NAMES_FILE, encoding='utf-8') as f:
                content = f.readlines()
            PersonNames().set([x.strip() for x in content])
        except Exception as e:
            print(str(e))

    @staticmethod
    def set_regions():
        try:
            with open(config.REGIONS_FILE, encoding='utf-8') as f:
                content = f.readlines()
            Regions().set([x.strip() for x in content])
        except Exception as e:
            print(str(e))

    @staticmethod
    def set_ranking():
        try:
            with open(config.RANKING_SCORE_FILE, encoding='utf-8') as f:
                content = f.readlines()
            RankingTable().set([x.strip().split(';') for x in content])
        except Exception as e:
            print(str(e))