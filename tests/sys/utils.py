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

    Utility methods for sys tests

"""

import io
import zipfile
from datetime import timedelta

import requests

from utils.migrate_plugins import create_new_metadata_record

REQUEST_TIMEOUT_SECONDS = timedelta(seconds=2).total_seconds()


def create_new_record_via_utils(config_fixture, stage=None):
    """
    Create initial metadata record via utils/new_plugin_record.sh
    This also acts as a check to ensure utils/new_plugin_record.sh is
    functioning as expected
    """
    config_fixture["secret"], config_fixture["hash"] = create_new_metadata_record(
        config_fixture["table_name"], config_fixture["plugin_id"], config_fixture["aws_region"], stage=stage
    )


def create_new_record(dynamodb_client_fixture, table, plugin_id, secret):
    """
    This can be used instead of the utils/new_plugin_record.sh script
    to add an initial plugin entry to the plugin metadata database
    """

    # Create version zero record
    dynamodb_client_fixture.put_item(
        TableName=table, Item={"id": {"S": plugin_id}, "item_version": {"S": "000000"}, "revisions": {"N": "0"}}
    )

    # Create metadata record
    dynamodb_client_fixture.put_item(
        TableName=table, Item={"id": {"S": plugin_id}, "item_version": {"S": "metadata"}, "secret": {"S": secret}}
    )


def get_mock_plugin(plugin_name, plugin_metadata):
    """
    Return a mock plugin for testing
    """

    inMemoryFile = io.BytesIO()
    with zipfile.ZipFile(inMemoryFile, "w") as archive:
        archive.writestr(f"{plugin_name}/test_plugin.py", "hello word")
        archive.writestr(f"{plugin_name}/metadata.txt", plugin_metadata)

    inMemoryFile.seek(0)
    return inMemoryFile.read()


def get_mock_plugin_no_metadata(plugin_name):
    """
    Create a mock plugin with no metadata file to allow
    testing of a invalid plugin
    """

    inMemoryFile = io.BytesIO()
    with zipfile.ZipFile(inMemoryFile, "w") as archive:
        archive.writestr(f"{plugin_name}/test_plugin.py", "hello word")

    inMemoryFile.seek(0)
    return inMemoryFile.read()


def post_plugin(base_url, stage, plugin_id, plugin, secret):
    header = {"Authorization": f"Bearer {secret}", "content-type": "application/octet-stream"}
    return requests.post(
        f"{base_url}plugin/{plugin_id}?stage={stage}", data=plugin, headers=header, timeout=REQUEST_TIMEOUT_SECONDS
    )


def retire_plugin(base_url, stage, plugin_id, secret):
    header = {"Authorization": f"Bearer {secret}", "content-type": "application/octet-stream"}
    return requests.delete(f"{base_url}plugin/{plugin_id}?stage={stage}", headers=header, timeout=REQUEST_TIMEOUT_SECONDS)


def ignore_keys(dictionary, ignore):
    """Some returned parameters such as 'updated_at' can not be
    easily predicted and therefore tested. This method is for
    removing such parameters prior to assert comparisons.
    """

    return dict((k, v) for k, v in dictionary.items() if k not in ignore)
