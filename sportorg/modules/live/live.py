import requests


class ResultProcess:
    def __init__(self, url, enabled=False):
        self.url = url
        self.enabled = enabled

    def send_race(self, race):
        pass

    def send_groups(self, groups):
        pass

    def send_persons(self, persons):
        pass

    def send_result(self, result):
        pass
