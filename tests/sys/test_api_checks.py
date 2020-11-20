import json
import requests


def test_ping(config_fixture):
    response = requests.get(f"{config_fixture['base_url']}ping")
    assert response.status_code == 200


def test_health(config_fixture):
    response = requests.get(f"{config_fixture['base_url']}health")
    assert response.status_code == 200
    assert json.loads(response.content) == json.loads(response.content)


def test_version(config_fixture):
    response = requests.get(f"{config_fixture['base_url']}version")
    return json.loads(response.content)
