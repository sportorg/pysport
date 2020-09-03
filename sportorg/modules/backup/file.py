from boltons.fileutils import atomic_rename

from . import binary, json


class File:
    BINARY = 'binary'
    JSON = 'json'

    def __init__(self, file_name, logger, ft='binary'):
        self._file_name = file_name
        self._logger = logger
        self._format = ft
        self._factory = {
            self.BINARY: binary,
            self.JSON: json,
        }
        self._factory_mode = {
            self.BINARY: 'wb',
            self.JSON: 'w',
        }
        self._factory_mode_read = {
            self.BINARY: 'rb',
            self.JSON: 'r',
        }

    @staticmethod
    def backup(file_name, func, mode='wb'):
        with open(file_name, mode) as f:
            func(f)

    def create(self):
        self._logger.info('Create ' + self._file_name)
        self.backup(
            self._file_name + '.tmp',
            self._factory[self._format].dump,
            self._factory_mode[self._format],
        )
        atomic_rename(self._file_name + '.tmp', self._file_name, overwrite=True)

    def save(self):
        self._logger.info('Save ' + self._file_name)
        self.backup(
            self._file_name + '.tmp',
            self._factory[self._format].dump,
            self._factory_mode[self._format],
        )
        atomic_rename(self._file_name + '.tmp', self._file_name, overwrite=True)

    def open(self):
        self._logger.info('Open ' + self._file_name)
        self.backup(
            self._file_name,
            self._factory[self._format].load,
            self._factory_mode_read[self._format],
        )
