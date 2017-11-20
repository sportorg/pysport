import logging
from . import bin
from . import formats
from sportorg.core.event import add_event


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


def backup(file, func, mode='wb'):
    with open(file, mode) as f:
        func(f)


def event_create(file):
    logging.debug('Create ' + file)
    backup(file, lambda f: bin.dump(f, True))


def event_dump(file):
    logging.debug('Dump ' + file)
    backup(file, bin.dump)


def event_load(file):
    logging.debug('Load ' + file)
    backup(file, bin.load, 'rb')


def init():
    add_event('create_file', event_create)
    add_event('dump', event_dump)
    add_event('load', event_load)

