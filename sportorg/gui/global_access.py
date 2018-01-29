import time

from sportorg.core.singleton import Singleton


class GlobalAccess(metaclass=Singleton):
    main_window = None

    def set_main_window(self, window):
        self.main_window = window

    def get_main_window(self):
        """

        :return: MainWindow
        """
        return self.main_window


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
