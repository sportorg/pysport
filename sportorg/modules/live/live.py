from functools import partial
from threading import Thread

import logging
import requests

from sportorg.models.memory import race
from sportorg.modules.live import orgeo
from sportorg.common.broker import Broker


class LiveClient:
    def init(self):
        Broker().subscribe('teamwork_recieving', self.send)
        Broker().subscribe('teamwork_sending', self.send)
        Broker().subscribe('teamwork_deleting', self.delete)

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

        if not isinstance(data, list):
            data = [data]
        items = []
        for item in data:
            if isinstance(item, dict):
                items.append(item)
            else:
                items.append(item.to_dict())

        #logging.debug('Orgeo send items: {}'.format(items))
        urls = self.get_urls()
        race_data = race().to_dict()
        for url in urls:
            func = partial(orgeo.create, requests, url, items, race_data, logging.root)
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
