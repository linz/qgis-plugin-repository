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

import uuid
import datetime
import json
import tempfile
import configparser
import pytest
from src.plugin.metadata_model import MetadataModel, ModelEncoder


def test_default():
    """
    Test json formatting of metadata model data
    """

    j = {
        "cfac5e5d-606a-4144-affc-13c716815985": {
            "created_at": datetime.datetime(2019, 9, 30, 1, 16, 14, 596744, tzinfo=datetime.timezone.utc),
            "deprecated": "False",
            "experimental": "False",
            "updated_at": datetime.datetime(2019, 9, 30, 1, 16, 14, 596744, tzinfo=datetime.timezone.utc),
            "repository": "https://github.com/test",
        }
    }
    result = json.dumps(j, cls=ModelEncoder)
    assert result == json.dumps(
        {
            "cfac5e5d-606a-4144-affc-13c716815985": {
                "created_at": "2019-09-30T01:16:14.596744+00:00",
                "deprecated": "False",
                "experimental": "False",
                "updated_at": "2019-09-30T01:16:14.596744+00:00",
                "repository": "https://github.com/test",
            }
        }
    )


def test_metadata_model(mocker):
    """
    model parameters are set and save is executed
    without error
    """

    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")
    file_name = str(uuid.uuid4())

    metadata = {
        "id": "c611a73c-12a0-4414-9ab5-ed1889122073",
        "name": "test",
        "qgis_minimum_version": "0.0.0",
        "qgis_maximum_version": "0.0.1",
        "description": "this is a test",
        "about": "testing",
        "version": "1.0.0",
        "author_name": "me",
        "email": "me@theinternet.com",
        "changelog": "done stuff",
        "experimental": "True",
        "deprecated": "False",
        "tags": "test",
        "homepage": "plugin.com",
        "repository": "github/plugin",
        "tracker": "github/pluigin/issues",
        "icon": "icon.png",
        "category": "test",
        "file_name": file_name,
    }

    result = MetadataModel(
        id=metadata.get("id"),
        name=metadata.get("name"),
        qgis_minimum_version=metadata.get("qgis_minimum_version"),
        qgis_maximum_version=metadata.get("qgis_maximum_version"),
        description=metadata.get("description"),
        about=metadata.get("about"),
        version=metadata.get("version"),
        author_name=metadata.get("author_name"),
        email=metadata.get("email"),
        changelog=metadata.get("changelog"),
        experimental=metadata.get("experimental"),
        deprecated=metadata.get("deprecated"),
        tags=metadata.get("tags"),
        homepage=metadata.get("homepage"),
        repository=metadata.get("repository"),
        tracker=metadata.get("tracker"),
        icon=metadata.get("icon"),
        category=metadata.get("category"),
        file_name=metadata.get("file_name"),
    )

    result.save()

    for key in metadata:
        print("assessing property: {0}".format(key))
        assert result.attribute_values[key] == metadata[key]


def test_metadata_model_missing_required(mocker):
    """
    pynamdodb model throws exception on save if
    required fields are null
    """

    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")

    metadata = {
        "id": "c611a73c-12a0-4414-9ab5-ed1889122073",
        "name": "test",
        "qgisMinimumVersion": "0.0.0",
        "qgisMaximumVersion": "0.0.1",
        "description": "this is a test",
        "about": "testing",
        "version": "1.0.0",
        "author": "me",
        "email": "me@theinternet.com",
    }

    result = MetadataModel(
        id=metadata.get("id"),
        updated_at=metadata.get("updated_at"),
        name=metadata.get("name"),
        qgis_minimum_version=metadata.get("qgisMinimumVersion"),
        qgis_maximum_version=metadata.get("qgisMaximumVersion"),
        description=metadata.get("description"),
        about=metadata.get("about"),
        version=metadata.get("version"),
        author_name=metadata.get("author"),
        email=metadata.get("email"),
        changelog=metadata.get("changelog"),
        experimental=metadata.get("experimental"),
        deprecated=metadata.get("deprecated"),
        tags=metadata.get("tags"),
        homepage=metadata.get("homepage"),
        repository=metadata.get("repository"),
        tracker=metadata.get("tracker"),
        icon=metadata.get("icon"),
        category=metadata.get("category"),
    )

    with pytest.raises(ValueError) as excinfo:
        result.save()
        assert "ValueError" in str(excinfo.value)


def test_json_dump_model(mocker):
    """
    Dump all metadata from model in json format
    """

    metadata_item_2019 = mocker.Mock()
    metadata_item_2018 = mocker.Mock()

    metadata_item_2019.id = "88f530e5-8914-4bf8-9351-f351e6b0e8fc"
    metadata_item_2019.created_at = datetime.datetime(2019, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc)
    metadata_item_2019.name = "Test_Plugin1"
    metadata_item_2019.attribute_values = {
        "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fc",
        "name": "Test_Plugin1",
        "created_at": datetime.datetime(2019, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc),
    }
    metadata_item_2018.id = "88f530e5-8914-4bf8-9351-f351e6b0e8fb"
    metadata_item_2018.created_at = datetime.datetime(2018, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc)
    metadata_item_2018.name = "Test_Plugin2"
    metadata_item_2018.attribute_values = {
        "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fb",
        "name": "Test_Plugin2",
        "created_at": datetime.datetime(2019, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc),
    }

    mocker.patch("src.plugin.metadata_model.MetadataModel.scan", return_value=[metadata_item_2019, metadata_item_2018])

    result = MetadataModel.json_dump_model()
    assert result == {
        "88f530e5-8914-4bf8-9351-f351e6b0e8fc": {
            "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fc",
            "name": "Test_Plugin1",
            "created_at": "2019-09-16T02:04:12.590806+00:00",
        },
        "88f530e5-8914-4bf8-9351-f351e6b0e8fb": {
            "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fb",
            "name": "Test_Plugin2",
            "created_at": "2019-09-16T02:04:12.590806+00:00",
        },
    }


def test_json_dump_item(mocker):
    """
    Dump single metadata item from model in json format
    """

    metadata_item = mocker.Mock()
    metadata_item.id = "88f530e5-8914-4bf8-9351-f351e6b0e8fc"
    metadata_item.attribute_values = {
        "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fc",
        "name": "Test_Plugin1",
        "created_at": datetime.datetime(2019, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc),
    }

    result = MetadataModel.json_dump_item(metadata_item)
    assert result == {
        "88f530e5-8914-4bf8-9351-f351e6b0e8fc": {
            "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fc",
            "name": "Test_Plugin1",
            "created_at": "2019-09-16T02:04:12.590806+00:00",
        }
    }


def test_json_dump_model_current(mocker):
    """
    Test when there are two database model objects only differing in data
    the method returns a representation of only the most current
    """

    metadata_item_2019 = mocker.Mock()
    metadata_item_2018 = mocker.Mock()
    metadata_item_2019.id = "88f530e5-8914-4bf8-9351-f351e6b0e8fc"
    metadata_item_2019.created_at = datetime.datetime(2019, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc)
    metadata_item_2019.name = "Test_Plugin"
    metadata_item_2019.version = "0.0.1"
    metadata_item_2019.attribute_values = {
        "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fc",
        "name": "Test_Plugin",
        "version": "0.0.1",
        "created_at": datetime.datetime(2019, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc),
    }
    metadata_item_2018.id = "88f530e5-8914-4bf8-9351-f351e6b0e8fb"
    metadata_item_2018.created_at = datetime.datetime(2018, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc)
    metadata_item_2018.name = "Test_Plugin"
    metadata_item_2018.version = "0.0.1"
    metadata_item_2018.attribute_values = {
        "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fb",
        "name": "Test_Plugin",
        "version": "0.0.1",
        "created_at": datetime.datetime(2019, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc),
    }

    mocker.patch("src.plugin.metadata_model.MetadataModel.scan", return_value=[metadata_item_2019, metadata_item_2018])

    result = MetadataModel.json_dump_model_current()
    assert result == {
        "Test_Plugin-0.0.1": {
            "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fc",
            "name": "Test_Plugin",
            "version": "0.0.1",
            "created_at": "2019-09-16T02:04:12.590806+00:00",
        }
    }


def test_updated_metadata_db(mocker):
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

    with tempfile.TemporaryFile(mode="w+t") as tmp:
        tmp.writelines(
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
qgisMinimumVersion=4.0.0"""
        )
        tmp.seek(0)
        config_parser = configparser.ConfigParser()
        config_parser.read_string(tmp.read())
        result = MetadataModel.update_metadata_db(config_parser, plugin_id, content_disposition)
    assert result is None


def test_updated_metadata_db_missing_field(mocker):
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
    with tempfile.TemporaryFile(mode="w+t") as tmp:
        tmp.writelines(
            """[general]
name=plugin
icon=icon.png
email=test@linz.govt.nz
author=Tester
description=Plugin for testing the repository
version=0.1
experimental=True
about=this is a test
repository=github/test"""
        )
        tmp.seek(0)
        config_parser = configparser.ConfigParser()
        config_parser.read_string(tmp.read())
        with pytest.raises(ValueError) as error:
            MetadataModel.update_metadata_db(config_parser, plugin_id, content_disposition)
    assert "Attribute 'qgis_minimum_version' cannot be None" in str(error.value)
