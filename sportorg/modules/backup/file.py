import gzip
import logging
from typing import Optional

from boltons.fileutils import atomic_rename

from sportorg import settings

from . import json

logger = logging.getLogger(__name__)


def is_gzip_file(file_name: str) -> bool:
    try:
        with gzip.open(file_name) as f:
            f.read(1)
        return True
    except gzip.BadGzipFile:
        return False


class File:
    def __init__(self, file_name: str):
        self._file_name = file_name
        self.use_utf8 = settings.SETTINGS.file_save_in_utf8
        self.use_gzip = settings.SETTINGS.file_save_in_gzip

    def _backup(self, file_name: str, func, mode: str = "r") -> None:
        # if user set UTF-8 usage, first try to open file in UTF-8,
        # then in system locale (1251 for RU Windows)
        use_utf8 = settings.SETTINGS.file_save_in_utf8
        use_gzip = settings.SETTINGS.file_save_in_gzip

        if mode == "r":
            use_gzip = is_gzip_file(file_name)

        def_encoding = "utf-8" if use_utf8 and not use_gzip else None
        if use_gzip:
            mode = f"{mode}+b"

        try:
            with open(file_name, mode, encoding=def_encoding) as f:
                func(f, compress=use_gzip)

        except UnicodeDecodeError:
            f.close()

            alt_encoding: Optional[str] = None if use_utf8 or use_gzip else "utf-8"

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
