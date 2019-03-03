import logging
import os
from queue import Queue
from threading import Thread

from playsound import playsound

from sportorg import config
from sportorg.common.singleton import singleton


def play(sound):
    playsound(sound)


def get_sounds(path=None):
    if path is None:
        path = config.SOUND_DIR
    files = []
    for p in os.listdir(path):
        full_path = os.path.join(path, p)
        if os.path.isdir(full_path):
            fs = get_sounds(full_path)
            for f in fs:
                files.append(f)
        else:
            files.append(full_path)

    return files


@singleton
class Audio(object):
    def __init__(self):
        self._queue = Queue()
        self._thread = None
        self._logger = logging.root

    def play(self, sound):
        self._queue.put(sound)
        self._start()

    def _start(self):
        if self._thread is None:
            self._thread = Thread(target=self._run, name=self.__class__.__name__)
            self._thread.start()
        elif not self._thread.is_alive():
            self._thread = None
            self._start()

    def _run(self):
        while not self._queue.empty():
            sound = self._queue.get()
            try:
                play(sound)
            except Exception as e:
                self._logger.error('Can not play {}'.format(sound))
                print(e)
