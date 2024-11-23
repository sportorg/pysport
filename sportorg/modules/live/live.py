import asyncio
import logging
import os
from functools import partial
from queue import Empty, Queue
from threading import Event, Thread

import aiohttp

from sportorg.models.memory import race
from sportorg.modules.live import orgeo

LIVE_TIMEOUT = int(os.getenv("SPORTORG_LIVE_TIMEOUT", "10"))


async def create_session(timeout: int) -> aiohttp.ClientSession:
    return aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout))


class LiveThread(Thread):
    def __init__(self):
        super().__init__(name="LiveThread", daemon=True)
        self._queue = Queue()
        self._stop_event = Event()
        self._delay = 0.5

    def send(self, func) -> None:
        self._queue.put_nowait(func)

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        session = loop.run_until_complete(create_session(LIVE_TIMEOUT))
        while not self._stop_event.is_set():
            try:
                funcs = []
                while True:
                    try:
                        funcs.append(self._queue.get_nowait())
                        self._queue.task_done()
                    except Empty:
                        break
                if funcs:
                    loop.run_until_complete(
                        asyncio.gather(
                            *[func(session=session) for func in funcs],
                            return_exceptions=True,
                        )
                    )
                else:
                    self._stop_event.wait(self._delay)
            except Exception as e:
                logging.error("Error: %s", str(e))


class LiveClient:
    def __init__(self):
        self._thread = LiveThread()

    def init(self):
        self._thread.start()

    @staticmethod
    def is_enabled():
        obj = race()
        live_enabled = obj.get_setting("live_enabled", False)
        urls = obj.get_setting("live_urls", [])
        return live_enabled and urls

    @staticmethod
    def get_urls():
        obj = race()
        urls = obj.get_setting("live_urls", [])
        return urls

    def send(self, data):
        logging.debug("LiveClient.send started, data = %s", str(data))
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
            if race().get_setting("live_results_enabled", False):
                func = partial(orgeo.create, url, items, race_data, logging.root)
                self._thread.send(func)

            if race().get_setting("live_cp_enabled", False):
                func = partial(
                    orgeo.create_online_cp,
                    url,
                    items,
                    race_data,
                    logging.root,
                )
                self._thread.send(func)

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
            func = partial(orgeo.delete, url, items, race_data, logging.root)
            self._thread.send(func)


live_client = LiveClient()
