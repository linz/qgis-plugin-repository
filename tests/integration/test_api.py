"""
################################################################################
#
# Copyright 2019 Crown copyright (c)
# Land Information New Zealand and the New Zealand Government.
# All rights reserved
#
# This program is released under the terms of the 3 clause BSD license. See the
# LICENSE file for more information.
#
################################################################################
"""


import tempfile
import zipfile


def test_upload_no_data(client_fixture):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits no data as
    part of the post
    """

    result = client_fixture.post("/plugin")
    assert result.status_code == 400
    assert result.json["message"] == "No plugin file supplied"


def test_upload_no_metadata(client_fixture):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits plugin
    data that contains no metadata.txt
    """

    with tempfile.SpooledTemporaryFile() as tmp:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("plugin/testplugin.py", "print(hello word)")
        tmp.seek(0)
        zipped_bytes = tmp.read()

        result = client_fixture.post("/plugin", data=zipped_bytes, headers={"Authorization": "Bearer 12345"})
    assert result.status_code == 400
    assert result.json["message"] == "No metadata.txt file found in plugin directory"


def test_upload_not_a_zipfile(client_fixture):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits plugin
    data that is not a zipfile
    """

    result = client_fixture.post("/plugin", data=b"0011010101010", headers={"Authorization": "Bearer 12345"})
    assert result.status_code == 400
    assert result.json["message"] == "Plugin file supplied not a Zipfile"


def query_iter_obj(mocker):
    """
    Return pynamodb like iterator object
    """

    plugin_item = mocker.Mock()
    plugin_item.id = "test_plugin"
    plugin_item.about = "For testing"
    plugin_item.author_name = "Tester"
    plugin_item.category = "Raster"
    plugin_item.item_version = "0"
    plugin_item.revisions = "0"
    plugin_item.created_at = "2019-10-07T00:57:19.868970+00:00"
    plugin_item.deprecated = "False"
    plugin_item.description = "Test"
    plugin_item.email = "test@gmail"
    plugin_item.experimental = "False"
    plugin_item.file_name = "test"
    plugin_item.homepage = "http://github.com/test"
    plugin_item.icon = "icon.svg"
    plugin_item.id = "test_plugin"
    plugin_item.name = "test plugin"
    plugin_item.qgis_maximum_version = "4.00"
    plugin_item.qgis_minimum_version = "4.00"
    plugin_item.repository = "https://github.com/test"
    plugin_item.tags = "raster"
    plugin_item.tracker = "http://github.com/test/issues"
    plugin_item.updated_at = "2019-10-07T00:57:19.868980+00:00"
    plugin_item.version = "0.0.0"
    plugin_item.attribute_values = {
        "about": "For testing",
        "author_name": "Tester",
        "category": "Raster",
        "item_version": "0",
        "revisions": "0",
        "created_at": "2019-10-07T00:57:19.868970+00:00",
        "deprecated": "False",
        "description": "Test",
        "email": "test@gmail",
        "experimental": "False",
        "file_name": "test",
        "homepage": "http://github.com/test",
        "icon": "icon.svg",
        "id": "test_plugin",
        "name": "test plugin",
        "qgis_maximum_version": "4.00",
        "qgis_minimum_version": "4.00",
        "repository": "https://github.com/test",
        "tags": "raster",
        "tracker": "http://github.com/test/issues",
        "updated_at": "2019-10-07T00:57:19.868980+00:00",
        "version": "0.0.0",
    }

    li = [plugin_item]
    for i in li:
        yield i


def test_upload_data(mocker, client_fixture):
    """
    When the users submits the correct plugin data
    test API responds indicating success.

    This test is at the integration level
    """

    mocker.patch("src.plugin.metadata_model.MetadataModel.query", return_value=query_iter_obj(mocker))
    mocker.patch("src.plugin.metadata_model.MetadataModel.validate_token")
    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")
    mocker.patch("src.plugin.metadata_model.MetadataModel.save")
    mocker.patch(
        "botocore.client.BaseClient._make_api_call",
        return_value={
            "ResponseMetadata": {
                "RequestId": "3C22AE855B7F5A33",
                "HostId": "ZXHuIMsJrekOxPq3BfgO0qT+K+dTcjqASxyR4zQTX",
                "HTTPStatusCode": 200,
                "HTTPHeaders": {
                    "x-amz-id-2": "ZXHuIMsJrekOxPq3BfgO0qT+K+dTcjqASxyR4zQTXcPHTAkXVB+=",
                    "x-amz-request-id": "3C22AE855B7F5A33",
                    "date": "Thu, 29 Aug 2019 22:16:58 GMT",
                    "etag": '"55fb20a4577fb47ed847033592026cad"',
                    "content-length": "0",
                    "server": "AmazonS3",
                },
                "RetryAttempts": 0,
            },
            "ETag": '"55fb20a4577fb47ed847033592026cad"',
        },
    )

    with tempfile.SpooledTemporaryFile() as tmp:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("test_plugin/test_plugin.py", "hello word")
            archive.writestr(
                "test_plugin/metadata.txt",
                """[general]
name=test plugin
icon=icon.png
email=test@linz.govt.nz
author=Tester
description=Plugin for testing the repository
version=0.1
experimental=True
about=this is a test
repository=github/test
qgisMinimumVersion=4.0.0""",
            )

        tmp.seek(0)
        zipped_bytes = tmp.read()
        result = client_fixture.post("/plugin", data=zipped_bytes, headers={"Authorization": "Bearer 12345"})
    assert result.status_code == 201
    assert result.get_json() == {
        "about": "For testing",
        "author_name": "Tester",
        "category": "Raster",
        "item_version": "0",
        "revisions": "0",
        "created_at": "2019-10-07T00:57:19.868970+00:00",
        "deprecated": "False",
        "description": "Test",
        "email": "test@gmail",
        "experimental": "False",
        "file_name": "test",
        "homepage": "http://github.com/test",
        "icon": "icon.svg",
        "id": "test_plugin",
        "name": "test plugin",
        "qgis_maximum_version": "4.00",
        "qgis_minimum_version": "4.00",
        "repository": "https://github.com/test",
        "tags": "raster",
        "tracker": "http://github.com/test/issues",
        "updated_at": "2019-10-07T00:57:19.868980+00:00",
        "version": "0.0.0",
    }
