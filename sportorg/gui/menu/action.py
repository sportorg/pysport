from abc import abstractmethod


class Action:
    def __init__(self):
        self.app = None

    @abstractmethod
    def execute(self):
        pass
