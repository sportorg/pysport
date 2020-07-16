import pytest

from sportorg import config


@pytest.fixture()
def data():
    with open('sportorg.iss') as f:
        yield f.readlines()


def test_app_version(data):
    for item in data:
        if '#define MyAppVersion ' in item:
            assert str(config.VERSION) in item
            return
    assert False, 'Not app version'


def test_version_info(data):
    for item in data:
        if '#define MyVersionInfoVersion ' in item:
            assert config.VERSION.file in item
            return
    assert False, 'Not version info'
