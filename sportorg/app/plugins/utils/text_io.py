from enum import Enum


class Data:
    def __init__(self):
        self.bib = ''
        self.start_time = ''
        self.finish_time = ''
        self.penalty = ''
        self.ard_number = ''

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
    def __init__(self, **kwargs):
        self.separator = ' '
        self.data_list = []
        self.identifier = EIdentifier.BIB
        self.value = EValue.START_TIME
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
