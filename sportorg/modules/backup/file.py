from . import binary


class File:
    def __init__(self, file_name, logger):
        self._file_name = file_name
        self._logger = logger

    @staticmethod
    def backup(file_name, func, mode='wb'):
        with open(file_name, mode) as f:
            func(f)

    def create(self):
        self._logger.info('Create ' + self._file_name)
        self.backup(self._file_name, binary.dump)

    def save(self):
        self._logger.info('Save ' + self._file_name)
        self.backup(self._file_name, binary.dump)

    def open(self):
        self._logger.info('Open ' + self._file_name)
        self.backup(self._file_name, binary.load, 'rb')
