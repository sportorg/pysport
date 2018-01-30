import time

from sportorg.core.singleton import Singleton


class GlobalAccess(metaclass=Singleton):
    def __init__(self):
        self.app = None

    def set_app(self, app):
        self.app = app

    def get_app(self):
        return self.app

    def get_main_window(self):
        return self.app.get_main_window()


class NumberClicker(metaclass=Singleton):
    def __init__(self):
        self.key = ''
        self.time = time.time()

    def click(self, number):
        t = time.time()
        if t - self.time < 0.8:
            self.time = t
            self.key += str(number)
            return int(self.key)
        self.time = t
        self.key = str(number)
        return int(number)
