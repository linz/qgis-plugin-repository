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

import pytest
from botocore.stub import ANY
from src.plugin import api


def test_format_error():
    """
    Test to ensure correct error formatting
    """

    expected_result = {"message": "This is an error"}

    result = api.format_error("This is an error", 400)

    assert expected_result == result.get_json()
    assert result.status_code == 400


def test_format_response():
    """
    Test to ensure correct response formatting
    """

    expected_result = {"plugin_name": "test_plugin"}

    result = api.format_response({"plugin_name": "test_plugin"}, 201)

    assert expected_result == result.get_json()
    assert result.status_code == 201


def test_get_metadata_path(plugin_zipfile_fixture):
    """
    Test that the method returns the metadata.txt path
    found within the plugin test data
    """

    result = api.get_metadata_path(plugin_zipfile_fixture)
    assert result == ["test_plugin/metadata.txt"]


def test_get_metadata_path_no_md(plugin_zipfile_no_md_fixture):
    """
    Test that the method returns an empty list when
    the plugin is missing the metadata.txt file
    """

    result = api.get_metadata_path(plugin_zipfile_no_md_fixture)
    assert result == []


def test_metadata_contents(plugin_zipfile_fixture):
    """
    Test the method extracts the metadata contents
    """

    result = api.metadata_contents(plugin_zipfile_fixture, "test_plugin/metadata.txt")
    assert result["general"]["name"] == "Testplugin"
    assert result["general"]["qgisMinimumVersion"] == "4.0"
    assert result["general"]["version"] == "0.1"
    assert result["general"]["description"] == "Plugin for testing the repository"


def test_upload_plugin_to_s3(s3_stub_fixture, global_data_fixture):
    """
    Test the upload_plugin_method returns
    the expected response on success
    """

    s3_stub_fixture.add_response(
        "put_object",
        expected_params={"Body": global_data_fixture["data"], "Bucket": "test_bucket", "Key": "test_plugin"},
        service_response=global_data_fixture["response"],
    )

    result = api.upload_plugin_to_s3(global_data_fixture["data"], "test_bucket", "test_plugin")

    assert result is True


def test_upload_file_to_s3_error(s3_stub_fixture):
    """
    Test the upload_plugin_method returns
    the expected response on error
    """

    s3_stub_fixture.add_client_error(
        "put_object", expected_params={"Body": ANY, "Bucket": "test_bucket", "Key": "test_plugin"}, service_error_code="404"
    )

    result = api.upload_plugin_to_s3("Durpa Durpa", "test_bucket", "test_plugin")
    assert result is False


def test_upload_no_data(client_fixture):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits no data as
    part of the post
    """

    result = client_fixture.post("/plugin")
    assert result.status_code == 400
    assert result.get_json() == {"message": "No plugin file supplied"}


def test_upload_no_stubmetadata(client_fixture, global_data_fixture):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits plugin
    data that contains no metadata.txt
    """

    with open(global_data_fixture["test_plugin_no_md"], "rb") as file_data:
        bytes_content = file_data.read()
    result = client_fixture.post("/plugin", data=bytes_content)
    assert result.status_code == 400
    assert result.get_json() == {"message": "metadata.txt not found"}


def test_upload_not_a_zipfile(client_fixture, global_data_fixture):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits plugin
    data that is not a zipfile
    """

    result = client_fixture.post("/plugin", data=global_data_fixture["test_file_not_a_zipfile"])
    assert result.status_code == 400
    assert result.get_json() == {"message": "File must be a zipfile"}


def test_upload_data(client_fixture, s3_stub_fixture, global_data_fixture):
    """
    When the users submits the correct plugin data
    test API responds indicating success.

    This test is at the integration level
    """

    with open(global_data_fixture["test_plugin"], "rb") as file_data:
        bytes_content = file_data.read()

    s3_stub_fixture.add_response(
        "put_object",
        expected_params={"Body": bytes_content, "Bucket": "qgis-plugin-repository", "Key": "Testplugin0.1"},
        service_response=global_data_fixture["response"],
    )

    result = client_fixture.post("/plugin", data=bytes_content)
    assert result.status_code == 201
    assert result.get_json() == {"pluginName": "Testplugin0.1"}


if __name__ == "__main__":
    pytest.main()
