import datetime
import logging

from sportorg.common.singleton import singleton


class Consumer:
    def __init__(self, call=None, priority=0):
        self.call = call
        self.priority = priority
        self._consumers = []

    def set_consumers(self, consumers):
        self._consumers = consumers
        return self

    def subscribe(self, call):
        self.call = call
        self._consumers.append(self)
        self._consumers.sort(key=lambda c: c.priority, reverse=True)
        return self


@singleton
class Broker(object):
    def __init__(self):
        self._consumers = {}
        self._logger = logging.root

    def add(self, name, priority=0):
        if name not in self._consumers:
            self._consumers[name] = []
        return Consumer(priority=priority).set_consumers(self._consumers[name])

    def subscribe(self, name, call, priority=0):
        return self.add(name, priority).subscribe(call)

    def produce(self, name, *args, **kwargs):
        logging.debug(str(datetime.datetime.now()) + ' Broker.produce started for ' + name)
        if name not in self._consumers:
            logging.debug(str(datetime.datetime.now()) + ' Broker.produce finished (no consumers) for ' + name)
            return None

        if not isinstance(self._consumers[name], list):
            logging.debug(str(datetime.datetime.now()) + ' Broker.produce finished (no consumers) for ' + name)
            return None

        result = []
        for consumer in self._consumers[name]:
            if not isinstance(consumer.call, tuple):
                r = consumer.call(*args, **kwargs)
            else:
                cls = consumer.call[0]
                method_name = consumer.call[1]
                try:
                    method = getattr(cls, method_name)
                    r = method(*args, **kwargs)
                except AttributeError:
                    self._logger.error(
                        'Class `{}` does not implement `{}`'.format(
                            cls.__class__.__name__, method_name
                        )
                    )
                    r = None

            if r:
                result.append(r)

        logging.debug(str(datetime.datetime.now()) + ' Broker.produce finished for ' + name)
        return result if len(result) else None
