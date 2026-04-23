import re

import pytest

from sportorg import config


@pytest.fixture()
def data():
    with open("sportorg.iss") as f:
        yield f.readlines()


def _stable_version(version: str) -> str:
    return re.sub(r"(a|b|rc)\d+$", "", version)


def test_app_version(data):
    version = _stable_version(str(config.VERSION))
    for item in data:
        if "#define MyAppVersion " in item:
            assert version in item
            return
    assert False, "Not app version"


def test_version_info(data):
    version = _stable_version(str(config.VERSION))[1:]
    for item in data:
        if "#define MyVersionInfoVersion " in item:
            assert f"{version}.0" in item
            return
    assert False, "Not version info"
