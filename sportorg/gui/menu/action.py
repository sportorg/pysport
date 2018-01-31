import logging
from abc import abstractmethod


class Action:
    def __init__(self):
        self.app = None

    @property
    def id(self):
        return ''

    def callback(self):
        try:
            self.execute()
        except Exception as e:
            logging.exception(str(e))

    @abstractmethod
    def execute(self):
        pass
