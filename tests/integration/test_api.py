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
    assert result.status_code == 500
    assert result.get_json() == {"message": "No plugin file supplied"}


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
        result = client_fixture.post("/plugin", data=zipped_bytes)
    assert result.status_code == 500
    assert result.get_json() == {"message": "No metadata.txt file found in plugin directory"}


def test_upload_not_a_zipfile(client_fixture):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits plugin
    data that is not a zipfile
    """

    result = client_fixture.post("/plugin", data=b"0011010101010")
    assert result.status_code == 500
    assert result.get_json() == {"message": "Plugin file supplied not a Zipfile"}


def test_upload_data(mocker, client_fixture):
    """
    When the users submits the correct plugin data
    test API responds indicating success.

    This test is at the integration level
    """
    mock_uuid = "88f530e5-8914-4bf8-9351-f351e6b0e8fc"
    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")
    plugin_item = mocker.Mock()
    plugin_item.id = "139735175778432"
    plugin_item.attribute_values = {
        "about": "For testing",
        "author_name": "Tester",
        "category": "Raster",
        "created_at": "2019-10-07T00:57:19.868970+00:00",
        "deprecated": "False",
        "description": "Test",
        "email": "test@gmail",
        "experimental": "False",
        "file_name": "test",
        "homepage": "http://github.com/test",
        "icon": "icon.svg",
        "id": "d41f5e33-d07d-4797-afec-ffca6ace7687",
        "name": "Value Tool",
        "qgis_maximum_version": "4.00",
        "qgis_minimum_version": "4.00",
        "repository": "https://github.com/test",
        "tags": "raster",
        "tracker": "http://github.com/test/issues",
        "updated_at": "2019-10-07T00:57:19.868980+00:00",
        "version": "0.0.0",
    }

    mocker.patch("src.plugin.metadata_model.MetadataModel.get", return_value=plugin_item)
    mocker.patch("uuid.uuid4", return_value=mock_uuid)
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
            archive.writestr("plugin/testplugin.py", "print(hello word)")
            archive.writestr(
                "plugin/metadata.txt",
                """[general]
name=plugin
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
        result = client_fixture.post("/plugin", data=zipped_bytes)
    assert result.status_code == 201
    assert result.get_json() == {
        "139735175778432": {
            "about": "For testing",
            "author_name": "Tester",
            "category": "Raster",
            "created_at": "2019-10-07T00:57:19.868970+00:00",
            "deprecated": "False",
            "description": "Test",
            "email": "test@gmail",
            "experimental": "False",
            "file_name": "test",
            "homepage": "http://github.com/test",
            "icon": "icon.svg",
            "id": "d41f5e33-d07d-4797-afec-ffca6ace7687",
            "name": "Value Tool",
            "qgis_maximum_version": "4.00",
            "qgis_minimum_version": "4.00",
            "repository": "https://github.com/test",
            "tags": "raster",
            "tracker": "http://github.com/test/issues",
            "updated_at": "2019-10-07T00:57:19.868980+00:00",
            "version": "0.0.0",
        }
    }


def test_upload_data_exception(mocker, client_fixture):
    """
    When s3_put error is encountered this should
    be captured by the plugin as an 500

    This test is at the integration level
    """

    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")

    result = client_fixture.post(
        "/plugin", data=(b"PK\x05\x06\x00\x00\x00\x00\x04\x00\x04\x00\x8e\x01\x00\x00\xa2\t\x00\x00\x00\x00")
    )

    assert result.status_code == 500
