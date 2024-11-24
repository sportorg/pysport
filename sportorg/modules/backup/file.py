import gzip
import logging
from typing import Optional

from boltons.fileutils import atomic_rename

from sportorg.modules.configs.configs import Config

from . import json

logger = logging.getLogger(__name__)


class File:
    def __init__(self, file_name: str):
        self._file_name = file_name
        self.use_utf8 = Config().configuration.get("save_in_utf8", False)
        self.use_gzip = Config().configuration.get("save_in_gzip", False)

    def _backup(self, file_name: str, func, mode: str = "r") -> None:
        use_utf8 = self.use_utf8
        use_gzip = self.use_gzip
        # if user set UTF-8 usage, first try to open file in UTF-8,
        # then in system locale (1251 for RU Windows)

        if mode == "r":
            try:
                with gzip.open(file_name) as f:
                    f.read(1)
                use_gzip = True
            except gzip.BadGzipFile:
                use_gzip = False

        def_encoding = "utf-8" if use_utf8 else None
        if use_gzip:
            mode = f"{mode}+b"

        try:
            with open(file_name, mode, encoding=def_encoding) as f:
                func(f, compress=use_gzip)

        except UnicodeDecodeError:
            f.close()

            alt_encoding: Optional[str] = "utf-8" if use_utf8 else None

            with open(file_name, mode, encoding=alt_encoding) as f:
                func(f, compress=use_gzip)

    def create(self) -> None:
        logger.info("Create " + self._file_name)
        self._backup(
            self._file_name + ".tmp",
            json.dump,
            "w",
        )
        atomic_rename(self._file_name + ".tmp", self._file_name, overwrite=True)

    def save(self) -> None:
        logger.info("Save " + self._file_name)
        self._backup(
            self._file_name + ".tmp",
            json.dump,
            "w",
        )
        atomic_rename(self._file_name + ".tmp", self._file_name, overwrite=True)

    def open(self) -> None:
        logger.info("Open " + self._file_name)
        self._backup(
            self._file_name,
            json.load,
            "r",
        )
