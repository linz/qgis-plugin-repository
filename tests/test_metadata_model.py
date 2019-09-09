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
from src.plugin.metadata_model import MetadataModel


def test_metadata_model(mocker):
    """
    model parameters are set and save is executed
    without error
    """

    mocker.patch("pynamodb.connection.base.get_session")
    mocker.patch("pynamodb.connection.table.Connection")
    mocker.patch("pynamodb.models.Model._meta_table")

    metadata = {
        "id": "c611a73c-12a0-4414-9ab5-ed1889122073",
        "plugin_id": "test.1.0.0",
        "name": "test",
        "qgisMinimumVersion": "0.0.0",
        "qgisMaximumVersion": "0.0.1",
        "description": "this is a test",
        "about": "testing",
        "version": "1.0.0",
        "author": "me",
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
    }

    result = MetadataModel(
        id=metadata.get("id"),
        plugin_id=metadata.get("plugin_id"),
        name=metadata.get("name"),
        qgisMinimumVersion=metadata.get("qgisMinimumVersion"),
        qgisMaximumVersion=metadata.get("qgisMaximumVersion"),
        description=metadata.get("description"),
        about=metadata.get("about"),
        version=metadata.get("version"),
        author=metadata.get("author"),
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
    mocker.patch("pynamodb.models.Model._meta_table")

    metadata = {
        "id": "c611a73c-12a0-4414-9ab5-ed1889122073",
        "plugin_id": "test.1.0.0",
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
        plugin_id=metadata.get("plugin_id"),
        name=metadata.get("name"),
        qgisMinimumVersion=metadata.get("qgisMinimumVersion"),
        qgisMaximumVersion=metadata.get("qgisMaximumVersion"),
        description=metadata.get("description"),
        about=metadata.get("about"),
        version=metadata.get("version"),
        author=metadata.get("author"),
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
