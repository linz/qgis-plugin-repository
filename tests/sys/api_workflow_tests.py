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

    API tests. These are not executed directly but wrapped by dev and prd
    plugin workflow tests.

"""


import io
import json
import xml.etree.ElementTree as ET
import zipfile

import requests

from .utils import (
    REQUEST_TIMEOUT_SECONDS,
    create_new_record_via_utils,
    get_mock_plugin,
    ignore_keys,
    post_plugin,
    retire_plugin,
)


def test_post_plugin(config_fixture, stage=""):
    """
    Test posting of a plugin. Will validate for both
    productions and development plugin workflows
    """

    create_new_record_via_utils(config_fixture, stage)

    plugin = get_mock_plugin(config_fixture["plugin_id"], config_fixture["plugin_metadata"])
    response = post_plugin(config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"])
    content = json.loads(response.content)

    exclude_from_checks = ["created_at", "file_name", "updated_at"]
    assert response.status_code == 201, response.content
    assert ignore_keys(content, exclude_from_checks) == ignore_keys(
        {
            "about": "this is a test",
            "author_name": "Yossarian",
            "deprecated": "False",
            "description": "Plugin for testing the repository",
            "email": "test@linz.govt.nz",
            "experimental": "True",
            "icon": "icon.png",
            "id": config_fixture["plugin_id"],
            "item_version": f"000001{stage}",
            "name": "test plugin",
            "qgis_maximum_version": "5.0.0",
            "qgis_minimum_version": "4.0.0",
            "repository": "github/test",
            "revisions": 1,
            "stage": stage,
            "version": "0.1",
        },
        (["stage"] if stage == "" else []),
    )
    assert content["created_at"] is not None
    assert content["file_name"] is not None
    assert content["updated_at"] is not None


def test_get_plugins(config_fixture, stage=""):
    """
    Test getting of previously posted plugin
    """

    # Get all plugins
    response = requests.get(f"{config_fixture['base_url']}plugin?stage={stage}", timeout=REQUEST_TIMEOUT_SECONDS)
    content = json.loads(response.content)

    # Search out the record just posted to ensure it is returned
    test_plugin = next((item for item in content if item["id"] == config_fixture["plugin_id"]))

    # check the test plugin is reported via the endpoint as expected
    assert response.status_code == 200, response.content
    assert ignore_keys(test_plugin, ["created_at", "file_name", "updated_at"]) == ignore_keys(
        {
            "about": "this is a test",
            "author_name": "Yossarian",
            "deprecated": "False",
            "description": "Plugin for testing the repository",
            "email": "test@linz.govt.nz",
            "experimental": "True",
            "icon": "icon.png",
            "id": config_fixture["plugin_id"],
            "item_version": f"000000{stage}",
            "name": "test plugin",
            "qgis_maximum_version": "5.0.0",
            "qgis_minimum_version": "4.0.0",
            "repository": "github/test",
            "revisions": 1,
            "stage": stage,
            "version": "0.1",
        },
        (["stage"] if stage == "" else []),
    )
    assert test_plugin["created_at"] is not None
    assert test_plugin["file_name"] is not None
    assert test_plugin["updated_at"] is not None


def test_revision_plugin(config_fixture, stage=""):
    """
    Create a new revision of the previously posted plugin.
    Ensure version numbers incremented.
    """

    plugin = get_mock_plugin(config_fixture["plugin_id"], config_fixture["plugin_metadata"])
    response = post_plugin(config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"])
    content = json.loads(response.content)

    assert ignore_keys(content, ["created_at", "file_name", "updated_at"]) == ignore_keys(
        {
            "about": "this is a test",
            "author_name": "Yossarian",
            "deprecated": "False",
            "description": "Plugin for testing the repository",
            "email": "test@linz.govt.nz",
            "experimental": "True",
            "icon": "icon.png",
            "id": config_fixture["plugin_id"],
            "item_version": f"000002{stage}",  # Note 2 revisions
            "name": "test plugin",
            "qgis_maximum_version": "5.0.0",
            "qgis_minimum_version": "4.0.0",
            "repository": "github/test",
            "revisions": 2,  # Note 2 revisions
            "stage": stage,
            "version": "0.1",
        },
        (["stage"] if stage == "" else []),
    )
    assert content["created_at"] is not None
    assert content["file_name"] is not None
    assert content["updated_at"] is not None


def test_retire_plugin(config_fixture, stage=""):
    """
    Retire the plugin
    """

    response = retire_plugin(config_fixture["base_url"], stage, config_fixture["plugin_id"], config_fixture["secret"])
    content = json.loads(response.content)

    assert response.status_code == 200, response.content

    # version 00000 should be enddated.
    assert content["ended_at"] is not None
    assert ignore_keys(content, ["created_at", "file_name", "updated_at", "ended_at"]) == ignore_keys(
        {
            "about": "this is a test",
            "author_name": "Yossarian",
            "deprecated": "False",
            "description": "Plugin for testing the repository",
            "email": "test@linz.govt.nz",
            "experimental": "True",
            "icon": "icon.png",
            "id": config_fixture["plugin_id"],
            "item_version": f"000003{stage}",
            "name": "test plugin",
            "qgis_maximum_version": "5.0.0",
            "qgis_minimum_version": "4.0.0",
            "repository": "github/test",
            "revisions": 3,
            "stage": stage,
            "version": "0.1",
        },
        (["stage"] if stage == "" else []),
    )
    assert content["created_at"] is not None
    assert content["file_name"] is not None
    assert content["updated_at"] is not None


def test_revive_plugin(config_fixture, stage=""):
    """
    test a retired plugin can be un-archived via uploading a new
    revision.
    """

    plugin_name = config_fixture["plugin_id"]
    plugin_metadata = config_fixture["plugin_metadata"]
    plugin = get_mock_plugin(plugin_name, plugin_metadata)
    post_plugin(config_fixture["base_url"], stage, config_fixture["plugin_id"], plugin, config_fixture["secret"])

    # Bug #114 is stopping testing against the above response.
    # While bug exists the below check is instead being used to
    # ensure the plugin was un-enddated

    # Get all plugins
    get_response = requests.get(f"{config_fixture['base_url']}plugin?stage={stage}", timeout=REQUEST_TIMEOUT_SECONDS)
    content = json.loads(get_response.content)

    # Search out the record just posted to ensure it is returned
    test_plugin = next((item for item in content if item["id"] == config_fixture["plugin_id"]))

    # check the test plugin is reported via the endpoint as expected
    assert get_response.status_code == 200
    assert ignore_keys(test_plugin, ["created_at", "file_name", "updated_at"]) == ignore_keys(
        {
            "about": "this is a test",
            "author_name": "Yossarian",
            "deprecated": "False",
            "description": "Plugin for testing the repository",
            "email": "test@linz.govt.nz",
            "experimental": "True",
            "icon": "icon.png",
            "id": config_fixture["plugin_id"],
            "item_version": f"000000{stage}",
            "name": "test plugin",
            "qgis_maximum_version": "5.0.0",
            "qgis_minimum_version": "4.0.0",
            "repository": "github/test",
            "revisions": 4,
            "stage": stage,
            "version": "0.1",
        },
        (["stage"] if stage == "" else []),
    )
    assert "ended_at" not in test_plugin
    assert test_plugin["created_at"] is not None
    assert test_plugin["file_name"] is not None
    assert test_plugin["updated_at"] is not None


def test_plugin_xml(config_fixture, stage=""):
    """
    Check the plugin metadata is returned as expected via the
    xml endpoint
    """

    if stage:
        url = f"{config_fixture['base_url']}/{stage}/plugins.xml"
    else:
        url = f"{config_fixture['base_url']}plugins.xml"

    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)

    assert response.status_code == 200, response.content
    tree = ET.ElementTree(ET.fromstring(response.text))
    root = tree.getroot()
    assert root.tag == "plugins"
    assert root.findtext("pyqgis_plugin/deprecated") == "False"
    assert root.findtext("pyqgis_plugin/experimental") == "True"
    assert root.findtext("pyqgis_plugin/repository") == "github/test"
    assert root.findtext("pyqgis_plugin/version") == "0.1"
    assert root.findtext("pyqgis_plugin/icon") == "icon.png"
    assert root.findtext("pyqgis_plugin/qgis_maximum_version") == "5.0.0"
    assert root.findtext("pyqgis_plugin/qgis_minimum_version") == "4.0.0"
    assert root.findtext("pyqgis_plugin/author_name") == "Yossarian"
    assert root.findtext("pyqgis_plugin/about") == "this is a test"
    assert root.findtext("pyqgis_plugin/description") == "Plugin for testing the repository"
    assert root.findtext("pyqgis_plugin/revisions") == "4"
    assert root.findtext("pyqgis_plugin/file_name") == f"{config_fixture['plugin_id']}.0.1.zip"


def test_download_plugin(config_fixture, stage=""):
    """
    Ensure the plugin can be download and the contents
    is as expected.
    """

    if stage:
        url = f"{config_fixture['base_url']}/{stage}/plugins.xml"
    else:
        url = f"{config_fixture['base_url']}plugins.xml"

    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    tree = ET.ElementTree(ET.fromstring(response.text))
    root = tree.getroot()
    download_url = root.findtext("pyqgis_plugin/download_url")
    assert download_url is not None

    # Download plugin
    r = requests.get(download_url, timeout=REQUEST_TIMEOUT_SECONDS)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        z.extractall()

        # Evaluate contents
        filename_list = z.namelist()
        assert f"{config_fixture['plugin_id']}/test_plugin.py" in filename_list
        assert f"{config_fixture['plugin_id']}/metadata.txt" in filename_list

        metadata = z.read(f"{config_fixture['plugin_id']}/metadata.txt").decode("utf-8")
        assert metadata == config_fixture["plugin_metadata"]
