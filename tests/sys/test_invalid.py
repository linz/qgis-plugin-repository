"""
################################################################################
#
#  LINZ QGIS plugin repository,
#  Crown copyright (c) 2020, Land Information New Zealand on behalf of
#  the New Zealand Government.
#
#  This file is released under the MIT licence. See the LICENCE file found
#  in the top-level directory of this distribution for more information.
#
################################################################################

    Test api invalid states

"""

import io
import json

import requests

from .utils import (
    REQUEST_TIMEOUT_SECONDS,
    create_new_record_via_utils,
    get_mock_plugin,
    get_mock_plugin_no_metadata,
    post_plugin,
)


def test_wrong_secrect(config_fixture, stage=""):
    secert = "wrongsecret"

    create_new_record_via_utils(config_fixture)

    plugin = get_mock_plugin(config_fixture["plugin_id"], config_fixture["plugin_metadata"])
    response = post_plugin(config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, secert)

    assert response.status_code == 403, response.content
    assert json.loads(response.content) == {"message": "Invalid token"}


def test_is_not_a_zipfile(config_fixture, stage=""):
    plugin = io.BytesIO(b"test").read()

    create_new_record_via_utils(config_fixture)
    response = post_plugin(config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"])
    assert response.status_code == 400, response.content
    assert json.loads(response.content) == {"message": "Plugin file supplied not a Zipfile"}


def test_no_data_supplied(config_fixture, stage=""):
    # File in me
    plugin = ""

    create_new_record_via_utils(config_fixture)
    response = post_plugin(config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"])
    assert response.status_code == 400, response.content
    assert json.loads(response.content) == {"message": "No plugin file supplied"}


def test_id_is_not_in_db(config_fixture, stage=""):
    plugin_id = "not_a_plugin_id"

    plugin = get_mock_plugin(config_fixture["plugin_id"], config_fixture["plugin_metadata"])
    response = post_plugin(config_fixture["base_url"], stage, plugin_id, plugin, config_fixture["secret"])
    assert response.status_code == 400, response.content
    assert json.loads(response.content) == {"message": "Plugin Not Found"}


def test_metadata_file_is_missing(config_fixture, stage=""):
    plugin = get_mock_plugin_no_metadata(config_fixture["plugin_id"])
    response = post_plugin(config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"])
    assert response.status_code == 400, response.content
    assert json.loads(response.content) == {"message": "No metadata.txt file found in plugin directory"}


def test_metadata_field_is_missing(config_fixture, stage=""):
    plugin = get_mock_plugin(config_fixture["plugin_id"], config_fixture["plugin_metadata"].replace("name", "nameo"))
    response = post_plugin(config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"])
    assert response.status_code == 400, response.content
    assert json.loads(response.content) == {"message": "Attribute 'name' cannot be None"}


def test_invalid_qgis_version(config_fixture):
    qgis_version = "v3"
    response = requests.get(f"{config_fixture['base_url']}plugins.xml?qgis={qgis_version}", timeout=REQUEST_TIMEOUT_SECONDS)

    assert response.status_code == 400, response.content
    assert json.loads(response.content) == {"message": "Invalid QGIS version"}


def test_stage_is_not_valid(config_fixture):
    stage = "testing"

    plugin = get_mock_plugin(config_fixture["plugin_id"], config_fixture["plugin_metadata"].replace("name", "nameo"))
    response = post_plugin(config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"])

    assert response.status_code == 400, response.content
    assert json.loads(response.content) == {"message": "stage is not recognised"}
