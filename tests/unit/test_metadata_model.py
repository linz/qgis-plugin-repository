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
        "id": "test_plugin",
        "item_version": 0,
        "revisions": 0,
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
        item_version=metadata.get("item_version"),
        revisions=metadata.get("revisions"),
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
