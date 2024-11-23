import logging
from typing import Optional

from boltons.fileutils import atomic_rename

from sportorg.modules.configs.configs import Config

from . import json

logger = logging.getLogger(__name__)


class File:
    def __init__(self, file_name: str):
        self._file_name = file_name

    @staticmethod
    def backup(file_name: str, func, mode: str = "r") -> None:
        use_utf8 = Config().configuration.get("save_in_utf8", False)
        # if user set UTF-8 usage, first try to open file in UTF-8,
        # then in system locale (1251 for RU Windows)
        try:
            def_encoding = None
            if use_utf8:
                def_encoding = "utf-8"

            with open(file_name, mode, encoding=def_encoding) as f:
                func(f)

        except UnicodeDecodeError:
            f.close()

            alt_encoding: Optional[str] = "utf-8"
            if use_utf8:
                alt_encoding = None

            with open(file_name, mode, encoding=alt_encoding) as f:
                func(f)

    def create(self) -> None:
        logger.info("Create " + self._file_name)
        self.backup(
            self._file_name + ".tmp",
            json.dump,
            "w",
        )
        atomic_rename(self._file_name + ".tmp", self._file_name, overwrite=True)

    def save(self) -> None:
        logger.info("Save " + self._file_name)
        self.backup(
            self._file_name + ".tmp",
            json.dump,
            "w",
        )
        atomic_rename(self._file_name + ".tmp", self._file_name, overwrite=True)

    def open(self) -> None:
        logger.info("Open " + self._file_name)
        self.backup(
            self._file_name,
            json.load,
            "r",
        )
