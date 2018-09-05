"""SportOrg Live Center"""


class LiveOrg:
    def __init__(self, requests, url, user_agent=None):
        if not user_agent:
            user_agent = 'SportOrg'
        self.requests = requests
        self._url = url
        self._headers = {
            'User-Agent': user_agent
        }

    def _get_url(self, text=''):
        return '{}{}'.format(self._url, text)

    def send(self, data):
        response = self.requests.post(
            self._get_url(),
            headers=self._headers,
            json=data
        )
        return response


CONFIG = {
    'type': 'live',
    'enabled': False,
}


def create(requests, url, data, race_data, logger=None):
    """
    data is Dict: Person, Result, Group, Course, Organization
    race_data is Dict: Race
    """
    global LiveOrg
    o = LiveOrg(requests, url)
    if not isinstance(data, list):
        data = [data]

    response = o.send(race_data)
    json_response = response.json()
    if 'status' in json_response:
        logger.info('Code: {}. {}'.format(response.status_code, json_response['status']))


def delete(requests, url, data, race_data, logger=None):
    """
    data is Dict: Person, Result, Group, Course, Organization
    race_data is Dict: Race
    """
    global LiveOrg
    o = LiveOrg(requests, url)
    if not isinstance(data, list):
        data = [data]

    response = o.send(race_data)
    json_response = response.json()
    if 'status' in json_response:
        logger.info('Code: {}. {}'.format(response.status_code, json_response['status']))
