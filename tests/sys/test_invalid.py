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

from tests.sys import utils
import pytest
import requests
import json
import io


def test_wrong_secrect(config_fixture, stage=""):

    secert = "wrongsecret"

    utils.create_new_record_via_utils(config_fixture)

    plugin = utils.get_mock_plugin(config_fixture["plugin_id"], config_fixture["plugin_metadata"])
    response = utils.post_plugin(config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, secert)

    assert response.status_code == 403
    assert json.loads(response.content) == {"message": "Invalid token"}


def test_is_not_a_zipfile(config_fixture, stage=""):

    plugin = io.BytesIO(b"test").read()

    utils.create_new_record_via_utils(config_fixture)
    response = utils.post_plugin(
        config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"]
    )
    assert response.status_code == 400
    assert json.loads(response.content) == {"message": "Plugin file supplied not a Zipfile"}


def test_no_data_supplied(config_fixture, stage=""):

    # File in me
    plugin = ""

    utils.create_new_record_via_utils(config_fixture)
    response = utils.post_plugin(
        config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"]
    )
    assert response.status_code == 400
    assert json.loads(response.content) == {"message": "No plugin file supplied"}


def test_id_is_not_in_db(config_fixture, stage=""):

    plugin_id = "not_a_plugin_id"

    plugin = utils.get_mock_plugin(config_fixture["plugin_id"], config_fixture["plugin_metadata"])
    response = utils.post_plugin(config_fixture["base_url"], stage, plugin_id, plugin, config_fixture["secret"])
    assert response.status_code == 400
    assert json.loads(response.content) == {"message": "Plugin Not Found"}


def test_metadata_file_is_missing(config_fixture, stage=""):

    plugin = utils.get_mock_plugin_no_metadata(config_fixture["plugin_id"])
    response = utils.post_plugin(
        config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"]
    )
    assert response.status_code == 400
    assert json.loads(response.content) == {"message": "No metadata.txt file found in plugin directory"}


def test_metadata_feild_is_missing(config_fixture, stage=""):

    config_fixture["plugin_metadata"]
    plugin = utils.get_mock_plugin(config_fixture["plugin_id"], config_fixture["plugin_metadata"].replace("name", "nameo"))
    response = utils.post_plugin(
        config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"]
    )
    assert response.status_code == 400
    assert json.loads(response.content) == {"message": "Attribute 'name' cannot be None"}


def test_invalid_qgis_version(config_fixture, stage=""):

    qgis_version = "v3"
    response = requests.get(f"{config_fixture['base_url']}plugins.xml?qgis={qgis_version}")

    assert response.status_code == 400
    assert json.loads(response.content) == {"message": "Invalid QGIS version"}


def test_stage_is_not_valid(config_fixture, stage=""):

    stage = "testing"

    plugin = utils.get_mock_plugin(config_fixture["plugin_id"], config_fixture["plugin_metadata"].replace("name", "nameo"))
    response = utils.post_plugin(
        config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"]
    )

    assert response.status_code == 400
    assert json.loads(response.content) == {"message": "stage is not recognised"}
