import logging
from threading import Thread
from functools import partial

import requests

from sportorg.common.singleton import Singleton
from sportorg.models.memory import race
from sportorg.modules.live import orgeo



class LiveClient(metaclass=Singleton):
    @staticmethod
    def is_enabled():
        obj = race()
        live_enabled = obj.get_setting('live_enabled', False)
        urls = obj.get_setting('live_urls', [])
        return live_enabled and urls

    @staticmethod
    def get_urls():
        obj = race()
        urls = obj.get_setting('live_urls', [])
        return urls

    def send(self, data):
        if not self.is_enabled():
            return

        urls = self.get_urls()
        race_data = race().to_dict()
        for url in urls:
            func = partial(orgeo.create, requests, url, data, race_data, logging.root)
            Thread(target=func, name='LiveThread').start()

    def delete(self, data):
        if not self.is_enabled():
            return

        urls = self.get_urls()
        race_data = race().to_dict()
        for url in urls:
            func = partial(orgeo.create, requests, url, data, race_data, logging.root)
            Thread(target=func, name='LiveThread').start()
