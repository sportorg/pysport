from enum import Enum


class Data:
    bib = ''
    start_time = ''
    finish_time = ''
    penalty = ''
    card_number = ''

    def __init__(self, **kwargs):
        self.init(**kwargs)

    def init(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError


class EIdentifier(Enum):
    NAME = 1
    BIB = 2


class EValue(Enum):
    START_TIME = 1
    FINISH_TIME = 2
    PENALTY = 3
    COMMENT = 4
    CARD_NUMBER = 5


class TextIO:
    separator = ' '
    data_list = []
    identifier = EIdentifier.BIB
    value = EValue.START_TIME

    def __init__(self, **kwargs):
        self.init(**kwargs)

    def init(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError

    def read(self, file):
        return self

    def write(self, file):
        pass

    def get_text(self):
        pass


def parse(file, separator=' '):
    text_io = TextIO(separator=separator)

    return text_io.read(file)
