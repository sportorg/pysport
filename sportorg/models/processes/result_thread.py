import logging
import threading
import queue

from sportorg.core.singleton import Singleton
from sportorg.models.memory import race, Result


class StopCommand:
    pass


class ResultThread(threading.Thread, metaclass=Singleton):
    """Don`t working. Not use!"""
    def __init__(self):
        super().__init__()
        self.setName(self.__class__.__name__)
        if True:
            raise Exception('"{}" can notuse!'.format(self.name))
        self._queue = queue.Queue()

    def put_queue(self, data):
        if not self.is_alive():
            logging.warning('{} is not alive. Restarting...'.format(self.name))
            self.start()
        self._queue.put(data)

    def run(self):
        while True:
            data = self._queue.get()
            try:
                if isinstance(data, StopCommand):
                    logging.debug('{} stopping'.format(self.name))
                    break
                if isinstance(data, Result):
                    race().add_result(data)
                    logging.info('Result added')
                else:
                    logging.error('Result not added')
            except Exception as e:
                logging.error(str(e))
                break

    def stop(self):
        self.put_queue(StopCommand())
