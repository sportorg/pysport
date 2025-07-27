import logging
import sys
from multiprocessing import freeze_support

from sportorg.modules.configs.configs import Config, ConfigFile

try:
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError:
    from PySide2.QtWidgets import QApplication

from sportorg import config, settings
from sportorg.common.singleton import Singleton
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.main_window import MainWindow
from sportorg.language import generate_mo
from sportorg.models.constant import (
    PersonMiddleNames,
    PersonNames,
    RankingTable,
    Regions,
    RentCards,
    StatusComments,
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
        try:
            self.load_settings()
        except Exception as e:
            logging.exception("Error loading settings: %s", str(e))
        self.set_status_comments()
        self.set_names()
        self.set_middle_names()
        self.set_regions()
        self.set_ranking()
        self.set_rent_cards()
        self.main_window.show_window()
        sys.exit(self.app.exec_())

    @staticmethod
    def load_settings():
        _, exists = settings.load_settings_from_file()
        Config().read()
        if not exists:
            settings.SETTINGS.app_check_updates = Config().configuration.get(
                "check_updates", True
            )
            settings.SETTINGS.locale = Config().configuration.get(
                "current_locale", "ru_RU"
            )
            settings.SETTINGS.logging_level = Config().configuration.get(
                "logging_level", True
            )
            settings.SETTINGS.logging_window_row_count = Config().configuration.get(
                "log_window_row_count", True
            )
            settings.SETTINGS.window_show_toolbar = Config().configuration.get(
                "show_toolbar", True
            )
            settings.SETTINGS.window_geometry = Config().geometry.get("main", "01")
            settings.SETTINGS.window_dialog_path = Config().parser.get(
                ConfigFile.DIRECTORY, "dialog_default_dir", fallback=""
            )
            settings.SETTINGS.race_use_birthday = Config().configuration.get(
                "use_birthday", False
            )
            settings.SETTINGS.templates_path = Config().templates.get(
                "directory", config.TEMPLATE_DIR
            )
            print("Templates path:", settings.SETTINGS.templates_path)
            settings.SETTINGS.file_autosave_interval = Config().configuration.get(
                "autosave_interval", 0
            )
            settings.SETTINGS.file_save_in_utf8 = Config().configuration.get(
                "save_in_utf8", True
            )
            settings.SETTINGS.file_save_in_gzip = Config().configuration.get(
                "save_in_gzip", True
            )
            settings.SETTINGS.file_open_recent_file = Config().configuration.get(
                "open_recent_file", True
            )
            settings.SETTINGS.printer_main = Config().printer.get("main", "")
            settings.SETTINGS.printer_split = Config().printer.get("split", "")
            settings.SETTINGS.sound_enabled = Config().sound.get("enabled", False)
            settings.SETTINGS.sound_successful_path = Config().sound.get(
                "successful", config.sound_dir("ok.wav")
            )
            settings.SETTINGS.sound_unsuccessful_path = Config().sound.get(
                "unsuccessful", config.sound_dir("failure.wav")
            )
            settings.SETTINGS.sound_rented_card_enabled = Config().sound.get(
                "enabled_rented_card", True
            )
            settings.SETTINGS.sound_rented_card_path = Config().sound.get(
                "rented_card", config.sound_dir("rented_card.wav")
            )
            settings.SETTINGS.sound_enter_number_path = Config().sound.get(
                "enter_number", config.sound_dir("enter_number.wav")
            )
            settings.SETTINGS.ranking = Config().ranking.get_all() or {}
            settings.save_settings_to_file()

    @staticmethod
    def set_status_comments():
        try:
            with open(
                settings.SETTINGS.source_status_comments_path, encoding="utf-8"
            ) as f:
                content = f.readlines()
            StatusComments().set([x.strip() for x in content])

        except Exception as e:
            logging.exception(str(e))

        try:
            with open(
                settings.SETTINGS.source_status_default_comments_path, encoding="utf-8"
            ) as f:
                content = f.readlines()
            StatusComments().set_default_statuses(content)
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_names():
        try:
            with open(settings.SETTINGS.source_names_path, encoding="utf-8") as f:
                content = f.readlines()
            PersonNames().set([x.strip() for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_middle_names():
        try:
            with open(
                settings.SETTINGS.source_middle_names_path, encoding="utf-8"
            ) as f:
                content = f.readlines()
            PersonMiddleNames().set([x.strip() for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_regions():
        try:
            with open(settings.SETTINGS.source_regions_path, encoding="utf-8") as f:
                content = f.readlines()
            Regions().set([x.strip() for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_ranking():
        try:
            with open(
                settings.SETTINGS.source_ranking_score_path, encoding="utf-8"
            ) as f:
                content = f.readlines()
            RankingTable().set([x.strip().split(";") for x in content])
        except Exception as e:
            logging.exception(str(e))

    @staticmethod
    def set_rent_cards():
        try:
            with open(settings.SETTINGS.source_rent_cards_path, encoding="utf-8") as f:
                content = f.read()
            RentCards().set_from_text(content)
        except FileNotFoundError:
            pass
        except Exception as e:
            logging.exception(str(e))
