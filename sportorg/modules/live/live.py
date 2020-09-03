import logging
from threading import Thread

import requests

from sportorg.common.broker import Broker
from sportorg.common.scripts import SCRIPTS
from sportorg.common.singleton import Singleton
from sportorg.models.memory import race


class LiveClient(metaclass=Singleton):
    def init(self):
        Broker().subscribe('teamwork_recieving', self.send)
        Broker().subscribe('teamwork_sending', self.send)
        Broker().subscribe('teamwork_deleting', self.delete)

    @staticmethod
    def is_enabled():
        obj = race()
        live_enabled = obj.get_setting('live_enabled', False)
        url = obj.get_setting('live_url', '')
        return live_enabled and bool(url)

    @staticmethod
    def get_url():
        obj = race()
        url = obj.get_setting('live_url', '')
        return url

    def send(self, data):
        if self.is_enabled():
            url = self.get_url()
            race_data = race().to_dict()
            for s in SCRIPTS:
                if s.is_type('live') and s.is_enabled():
                    Thread(
                        target=lambda: s.call(
                            'create', requests, url, data, race_data, logging.root
                        ),
                        name='LiveThread',
                    ).start()
                    break

    def delete(self, data):
        if self.is_enabled():
            url = self.get_url()
            race_data = race().to_dict()
            for s in SCRIPTS:
                if s.is_type('live') and s.is_enabled():
                    Thread(
                        target=lambda: s.call(
                            'delete', requests, url, data, race_data, logging.root
                        ),
                        name='LiveThread',
                    ).start()
                    break
