from . import formats
from . import bin


def dump(file, file_format=None):
    file_format = get_default_format(file_format)
    if file_format is formats.BIN:
        bin.dump(file)


def load(file, file_format=None):
    file_format = get_default_format(file_format)
    if file_format is formats.BIN:
        bin.load(file)


def get_default_format(file_format):
    if file_format is None:
        file_format = formats.BIN

    return file_format
