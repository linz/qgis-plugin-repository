import json

import requests

from .utils import REQUEST_TIMEOUT_SECONDS


def test_ping(config_fixture):
    response = requests.get(f"{config_fixture['base_url']}ping", timeout=REQUEST_TIMEOUT_SECONDS)
    assert response.status_code == 200


def test_health(config_fixture):
    response = requests.get(f"{config_fixture['base_url']}health", timeout=REQUEST_TIMEOUT_SECONDS)
    assert response.status_code == 200
    assert json.loads(response.content) == json.loads(response.content)


def test_version(config_fixture):
    response = requests.get(f"{config_fixture['base_url']}version", timeout=REQUEST_TIMEOUT_SECONDS)
    return json.loads(response.content)
