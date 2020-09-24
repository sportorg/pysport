"""
https://developer.github.com/v3/
"""

import requests

VERSION = ''


def get_last_tag_name():
    r = requests.get(
        'https://api.github.com/repos/sportorg/pysport/releases/latest', timeout=5
    )
    body = r.json()
    return body['tag_name']


def get_version():
    global VERSION
    if not VERSION:
        VERSION = get_last_tag_name()
    return VERSION


def check_version(version):
    if not get_version():
        return True
    return str(version) == get_version()
