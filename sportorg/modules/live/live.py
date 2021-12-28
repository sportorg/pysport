import logging
from functools import partial
from threading import Thread

import requests

from sportorg.models.memory import race
from sportorg.modules.live import orgeo


class LiveClient:
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
        logging.debug('LiveClient.send started, data = ' + str(data))
        if not self.is_enabled():
            return

        if not isinstance(data, list):
            data = [data]
        items = [item.to_dict() for item in data]

        urls = self.get_urls()
        race_data = race().to_dict()
        for url in urls:
            func = partial(orgeo.create, requests, url, items, race_data)
            Thread(target=func, name='LiveThread').start()

    def delete(self, data):
        if not self.is_enabled():
            return

        if not isinstance(data, list):
            data = [data]
        items = [item.to_dict() for item in data]

        urls = self.get_urls()
        race_data = race().to_dict()
        for url in urls:
            func = partial(orgeo.delete, requests, url, items, race_data)
            Thread(target=func, name='LiveThread').start()


live_client = LiveClient()
