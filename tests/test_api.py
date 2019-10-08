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

from unittest.mock import Mock
import datetime
import pytest

# from src.plugin import api


def test_format_response(api_fixture):
    """
    Test to ensure correct response formatting
    """

    expected_result = {"plugin_name": "test_plugin"}

    result = api_fixture.format_response({"plugin_name": "test_plugin"}, 201)

    assert expected_result == result.get_json()
    assert result.status_code == 201


def test_get_metadata_path(api_fixture, plugin_zipfile_fixture):
    """
    Test that the method returns the metadata.txt path
    found within the plugin test data
    """

    result = api_fixture.get_metadata_path(plugin_zipfile_fixture)
    assert result == ["test_plugin/metadata.txt"]


def test_get_metadata_path_no_md(api_fixture, plugin_zipfile_no_md_fixture):
    """
    Test that the method returns an empty list when
    the plugin is missing the metadata.txt file
    """

    result = api_fixture.get_metadata_path(plugin_zipfile_no_md_fixture)
    assert result == []


def test_get_zipfile_root_dir(api_fixture, plugin_zipfile_fixture):
    """
    Test the extraction of the zipfile root dir
    """

    result = api_fixture.get_zipfile_root_dir(plugin_zipfile_fixture)
    assert result == (None, "test_plugin")


def test_metadata_contents(api_fixture, plugin_zipfile_fixture):
    """
    Test the method extracts the metadata contents
    """

    result = api_fixture.metadata_contents(plugin_zipfile_fixture, "test_plugin/metadata.txt")
    assert result["general"]["name"] == "Testplugin"
    assert result["general"]["qgisMinimumVersion"] == "4.0"
    assert result["general"]["version"] == "0.1"
    assert result["general"]["description"] == "Plugin for testing the repository"


def test_updated_metadata_db(mocker, api_fixture, metadata_fixture):
    """
    Test the return value of updated_metadata_db
    However, the value is a mock return - bit of a
    waste of time
    """

    # Mocker used rather than stubber
    # Due to stubber issue. One mock method must be selected
    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")
    mock_uuid = "88f530e5-8914-4bf8-9351-f351e6b0e8fc"
    plugin_id = mock_uuid

    content_disposition = "test_plugin"
    result = api_fixture.update_metadata_db(metadata_fixture, plugin_id, content_disposition)
    assert result is None


def test_updated_metadata_db_missing_field(mocker, api_fixture, metadata_invalid_fixture):
    """
    Test the return value of updated_metadata_db
    However, the value is a mock return - bit of a
    waste of time
    """

    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")
    mock_uuid = "88f530e5-8914-4bf8-9351-f351e6b0e8fc"
    plugin_id = mock_uuid

    content_disposition = "test_plugin"
    result = api_fixture.update_metadata_db(metadata_invalid_fixture, plugin_id, content_disposition)
    assert result == "ValueError: Attribute 'qgis_minimum_version' cannot be None"


def test_get_most_current_plugins_metadata(mocker, api_fixture):
    """
    Test when there are two database model objects only differing in data
    the method returns a representation of only the most current
    """

    mock1 = Mock
    mock2 = Mock
    mock1.id = "88f530e5-8914-4bf8-9351-f351e6b0e8fc"
    mock1.created_at = datetime.datetime(2019, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc)
    mock1.name = "Test_Plugin"
    mock1.attribute_values = {
        "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fc",
        "name": "Test_Plugin",
        "created_at": datetime.datetime(2019, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc),
    }
    mock2.id = "88f530e5-8914-4bf8-9351-f351e6b0e8fb"
    mock2.created_at = datetime.datetime(2018, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc)
    mock2.name = "Test_Plugin"
    mock2.attribute_values = {
        "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fb",
        "name": "Test_Plugin",
        "created_at": datetime.datetime(2019, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc),
    }

    mocker.patch("src.plugin.metadata_model.MetadataModel.scan", return_value=[mock1, mock2])

    result = api_fixture.get_most_current_plugins_metadata()
    assert result == {
        "88f530e5-8914-4bf8-9351-f351e6b0e8fb": {
            "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fb",
            "name": "Test_Plugin",
            "created_at": datetime.datetime(2019, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc),
        }
    }


def test_validate_user_data_no_data(api_fixture):
    """
    If not data return error
    """

    result = api_fixture.validate_user_data(None)
    assert result == "No plugin file supplied"


def test_validate_user_data_not_zip(api_fixture, global_data_fixture):
    """
    If data is not zip return error
    """

    with open(global_data_fixture["test_metadata_invalid"], "rb") as file_data:
        bytes_content = file_data.read()
        result = api_fixture.validate_user_data(bytes_content)
        assert result == "File must be a zipfile"


def test_validate_user_data_is_zip(api_fixture, global_data_fixture):
    """
    If data is valid return None
    """

    with open(global_data_fixture["test_plugin"], "rb") as file_data:
        bytes_content = file_data.read()
        result = api_fixture.validate_user_data(bytes_content)
        assert result is None


def test_upload_no_data(client_fixture):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits no data as
    part of the post
    """

    result = client_fixture.post("/plugins")
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
    result = client_fixture.post("/plugins", data=bytes_content)
    assert result.status_code == 400
    assert result.get_json() == {"message": "metadata.txt not found"}


def test_upload_not_a_zipfile(client_fixture, global_data_fixture):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits plugin
    data that is not a zipfile
    """

    result = client_fixture.post("/plugins", data=global_data_fixture["test_file_not_a_zipfile"])
    assert result.status_code == 400
    assert result.get_json() == {"message": "File must be a zipfile"}


def test_upload_data(mocker, client_fixture, s3_stub_fixture, global_data_fixture):
    """
    When the users submits the correct plugin data
    test API responds indicating success.

    This test is at the integration level
    """
    mock_uuid = "88f530e5-8914-4bf8-9351-f351e6b0e8fc"
    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")
    mocker.patch("uuid.uuid4", return_value=mock_uuid)

    with open(global_data_fixture["test_plugin"], "rb") as file_data:
        bytes_content = file_data.read()

    s3_stub_fixture.add_response(
        "put_object",
        expected_params={"Body": bytes_content, "Bucket": "dummy", "ContentDisposition": "test_plugin", "Key": mock_uuid},
        service_response=global_data_fixture["response"],
    )

    result = client_fixture.post("/plugins", data=bytes_content)
    assert result.status_code == 201
    assert result.get_json() == {"plugin_id": mock_uuid}


def test_upload_data_exception(mocker, client_fixture, global_data_fixture):
    """
    When s3_put error is encountered this should
    be captured by the plugin as an 500

    This test is at the integration level
    """

    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")

    with open(global_data_fixture["test_plugin"], "rb") as file_data:
        bytes_content = file_data.read()
        result = client_fixture.post("/plugins", data=bytes_content)

        assert result.status_code == 500


if __name__ == "__main__":
    pytest.main()
