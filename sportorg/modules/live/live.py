import requests


class Live:
    def __init__(self, url, token, user_agent, logger):
        if len(url) and url[-1] == '/':
            url = url[0: -1]
        self._url = url
        self._token = token
        self._headers = {
            'User-Agent': user_agent,
            'X-Token': self._token
        }
        self._logger = logger

    def _get_url(self, text=''):
        return '{}{}'.format(self._url, text)

    def send_race(self, race):
        response = requests.post(self._get_url('/race'), headers=self._headers)
        return response

    def send_groups(self, groups):
        response = requests.post(self._get_url('/groups'), headers=self._headers)
        return response

    def send_persons(self, persons):
        response = requests.post(
            self._get_url('/persons'),
            headers=self._headers,
            json=persons
        )
        return response
