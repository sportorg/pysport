import time

from sportorg.common.singleton import singleton


@singleton
class GlobalAccess:
    def __init__(self):
        self.app = None

    def set_app(self, app):
        self.app = app

    def get_app(self):
        return self.app

    def get_main_window(self):
        return self.app.get_main_window()
