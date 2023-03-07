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
"""

import uuid
import datetime
import json
import hashlib
import pytest
from src.plugin import metadata_model
from src.plugin.metadata_model import MetadataModel, ModelEncoder
from src.plugin.error import DataError


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
        "item_version": "000000",
        "revisions": "0",
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

    for key, value in metadata.items():
        assert result.attribute_values[key] == value


def test_update_version_zero_no_empty_string(mocker):
    """
    Test empty strings are not added to the actions
    """

    metadata = {
        "general": {
            "id": "test_plugin",
            "name": "test",
            "qgisMinimumVersion": "0.0.0",
            "qgisMaximumVersion": "0.0.1",
            "description": "this is a test",
            "about": "testing",
            "version": "1.0.0",
            "author": "me",
            "email": "me@theinternet.com",
            "tags": "raster",
        }
    }

    mocker.patch("pynamodb.models.Model.update")
    version_zero = mocker.Mock()
    version_zero.revisions = 0
    version_zero.ended_at = None
    version_zero.attribute_values = {}
    version_zero.updated_at = None
    version_zero.file_name = None

    MetadataModel.update_version_zero(metadata, version_zero, "c611a73c-12a0-4414-9ab5-ed1889122073")
    assert "tags" in [str(i.values[0]) for i in version_zero.mock_calls[0][2]["actions"] if i.format_string != "{0}"]


def test_update_version_zero_empty_string(mocker):
    """
    Test empty strings are not added to the actions
    """

    metadata = {
        "general": {
            "id": "test_plugin",
            "name": "test",
            "qgisMinimumVersion": "0.0.0",
            "qgisMaximumVersion": "0.0.1",
            "description": "this is a test",
            "about": "testing",
            "version": "1.0.0",
            "author": "me",
            "email": "me@theinternet.com",
            "tags": "",
        }
    }

    mocker.patch("pynamodb.models.Model.update")
    version_zero = mocker.Mock()
    version_zero.revisions = 0
    version_zero.ended_at = None
    version_zero.attribute_values = {}
    version_zero.updated_at = None
    version_zero.file_name = None

    MetadataModel.update_version_zero(metadata, version_zero, "c611a73c-12a0-4414-9ab5-ed1889122073")
    # check tags (value = empty string) did not make it in the actions
    assert "tags" not in [str(i.values[0]) for i in version_zero.mock_calls[0][2]["actions"] if i.format_string != "{0}"]


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


def query_iter_obj(mocker, secret):
    """
    Return pynamodb like iterator object
    """

    plugin_item = mocker.Mock()
    plugin_item.secret = secret

    li = [plugin_item]
    for i in li:
        yield i


def hash_token(token):
    """
    hash token for comparison
    """

    return hashlib.sha512(token.encode("utf-8")).hexdigest()


def test_validate_token(mocker):
    """
    Test successful matching of secret
    """

    token = "12345"
    plugin_stage = "dev"
    mocker.patch("src.plugin.metadata_model.MetadataModel.query", return_value=query_iter_obj(mocker, hash_token(token)))
    plugin_id = "test_plugin"
    MetadataModel.validate_token(token, plugin_id, plugin_stage)


def test_validate_token_incorrect_secret(mocker):
    """
    Fail if token does not match database secret
    """

    mocker.patch("src.plugin.metadata_model.MetadataModel.query", return_value=query_iter_obj(mocker, "54321"))
    mocker.patch("werkzeug.local.LocalProxy.__getattr__", return_value={"authorization": "basic 12345"})
    mocker.patch("src.plugin.log.g", return_value={"requestId": "1234567", "plugin_id": "test_plugin"})

    token = "12345"
    plugin_id = "test_plugin"
    plugin_stage = "dev"
    with pytest.raises(DataError) as error:
        MetadataModel.validate_token(token, plugin_id, plugin_stage)
    assert "Invalid token" in str(error.value)


def test_hash_token():
    """
    Test hashing is giving the expected result
    """

    token = "12345"
    # pylint: disable=line-too-long
    matching_hash = "3627909a29c31381a071ec27f7c9ca97726182aed29a7ddd2e54353322cfb30abb9e3a6df2ac2c20fe23436311d678564d0c8d305930575f60e2d3d048184d79"
    result = metadata_model.hash_token(token)
    assert result == matching_hash


def format_item_version_version_zero():
    """
    Test foramtting of item version string
    """

    plugin_stage = "dev"
    result = metadata_model.format_item_version(plugin_stage)
    assert result == "000000dev"


def format_item_version_prd():
    """
    Test foramtting of item version string
    """

    plugin_stage = ""
    result = metadata_model.format_item_version(plugin_stage)
    assert result == "000000"


def format_item_version_version_five():
    """
    Test foramtting of item version string
    """

    plugin_stage = "dev"
    item_version = "000005"
    result = metadata_model.format_item_version(plugin_stage, item_version)
    assert result == "000005dev"


def format_item_version_metadata():
    """
    Test foramtting of item version string
    """

    plugin_stage = "dev"
    result = metadata_model.format_item_version(plugin_stage)
    assert result == "metadatadev"
