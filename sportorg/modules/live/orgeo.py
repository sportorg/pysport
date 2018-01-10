import logging
from queue import Queue
from threading import Thread, main_thread

import requests

from sportorg import config
from sportorg.core.singleton import Singleton


class Command:
    def __init__(self, command, url='', data=None):
        self.command = command
        self.url = url
        self.data = data


class Orgeo:
    def __init__(self, user_agent=None, logger=None):
        if not user_agent:
            user_agent = 'Orgeo client'
        self._url = ''
        self._headers = {
            'User-Agent': user_agent
        }
        self._logger = logger

    def _get_url(self, text=''):
        return '{}{}'.format(self._url, text)

    def set_url(self, url):
        self._url = url
        return self

    def send(self, data):
        response = requests.post(
            self._get_url(),
            headers=self._headers,
            json=data
        )
        return response


class OrgeoThread(Thread):
    def __init__(self, queue, user_agent=None, logger=None):
        super().__init__(name='Orgeo')
        self._queue = queue
        self._user_agent = user_agent
        self._logger = logger

    def run(self):
        orgeo = Orgeo(self._user_agent, self._logger)
        while True:
            try:
                command = self._queue.get()
                if command.command == 'stop':
                    break
                if not main_thread().is_alive():
                    break
                # orgeo.set_url(command.url).send(command.data)
                # if not self._queue.qsize():
                #     break
            except Exception as e:
                self._logger.error(str(e))


class OrgeoClient(metaclass=Singleton):
    def __init__(self):
        self._queue = Queue()
        self._thread = None
        self._i = 0

    def _start_thread(self):
        if self._thread is None:
            self._thread = OrgeoThread(
                self._queue,
                '{} {}'.format(config.NAME, config.VERSION),
                logging.root
            )
            self._thread.start()
        elif not self._thread.is_alive():
            if self._i < 5:
                self._thread = None
                self._i += 1
                self._start_thread()
            else:
                print('Thread can not started')

    def send_result(self):
        self._start_thread()
        self._queue.put(Command('result', 'url', {}))
