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


def test_updated_metadata_db(mocker, metadata_fixture):
    """
    Test the return value of updated_metadata_db
    However, the value is a mock return - bit of a
    waste of time
    """

    # Mocker used rather than stubber
    # Due to stubber issue. One mock method must be selected
    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")
    mocker.patch("pynamodb.models.Model._meta_table")

    result = api.updated_metadata_db(metadata_fixture)
    assert result == (None, "Testplugin.0.1")


def test_updated_metadata_db_missing_field(mocker, metadata_invalid_fixture):
    """
    Test the return value of updated_metadata_db
    However, the value is a mock return - bit of a
    waste of time
    """

    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")
    mocker.patch("pynamodb.models.Model._meta_table")

    result = api.updated_metadata_db(metadata_invalid_fixture)
    assert result == ("ValueError: Attribute 'qgisMinimumVersion' cannot be None", "Testplugin.0.1")


def test_upload_no_data(client_fixture):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits no data as
    part of the post
    """

    result = client_fixture.post("/plugin")
    assert result.status_code == 400
    assert result.get_json() == {"message": "No plugin file supplied"}


def test_upload_no_metadata(client_fixture, global_data_fixture):
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


def test_upload_data(mocker, client_fixture, s3_stub_fixture, global_data_fixture):
    """
    When the users submits the correct plugin data
    test API responds indicating success.

    This test is at the integration level
    """

    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")
    mocker.patch("pynamodb.models.Model._meta_table")

    with open(global_data_fixture["test_plugin"], "rb") as file_data:
        bytes_content = file_data.read()

    s3_stub_fixture.add_response(
        "put_object",
        expected_params={"Body": bytes_content, "Bucket": "qgis-plugin-repository", "Key": "Testplugin.0.1"},
        service_response=global_data_fixture["response"],
    )

    result = client_fixture.post("/plugin", data=bytes_content)
    assert result.status_code == 201
    assert result.get_json() == {"pluginName": "Testplugin.0.1"}


def test_upload_data_exception(mocker, client_fixture, global_data_fixture):
    """
    When s3_put error is encountered this should
    be captured by the plugin as an 500

    This test is at the integration level
    """

    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")
    mocker.patch("pynamodb.models.Model._meta_table")

    with open(global_data_fixture["test_plugin"], "rb") as file_data:
        bytes_content = file_data.read()
        result = client_fixture.post("/plugin", data=bytes_content)

        assert result.status_code == 500


if __name__ == "__main__":
    pytest.main()
