import logging
from functools import partial
from threading import Thread

import requests

from sportorg.common.broker import Broker
from sportorg.models.memory import race
from sportorg.modules.live import orgeo


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
        logging.debug('LiveClient.send started, data = ' + str(data))
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

        urls = self.get_urls()
        race_data = race().to_dict()
        for url in urls:
            if race().get_setting('live_results_enabled', False):
                func = partial(
                    orgeo.create, requests, url, items, race_data, logging.root
                )
                Thread(target=func, name='LiveThread', daemon=True).start()

            if race().get_setting('live_cp_enabled', False):
                func = partial(
                    orgeo.create_online_cp,
                    requests,
                    url,
                    items,
                    race_data,
                    logging.root,
                )
                Thread(target=func, name='LiveThread_OnlineCP', daemon=True).start()

    def delete(self, data):
        if not self.is_enabled():
            return

        items = []
        for item in data:
            if isinstance(item, dict):
                items.append(item)
            else:
                items.append(item.to_dict())

        urls = self.get_urls()
        race_data = race().to_dict()
        for url in urls:
            func = partial(orgeo.delete, requests, url, items, race_data)
            Thread(target=func, name='LiveThread', daemon=True).start()


live_client = LiveClient()
