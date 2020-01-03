import logging
from abc import abstractmethod


class Action:
    def __init__(self, app):
        self.app = app

    def __call__(self):
        try:
            self.execute()
        except Exception as e:
            logging.error(str(e))

    @abstractmethod
    def execute(self):
        pass
