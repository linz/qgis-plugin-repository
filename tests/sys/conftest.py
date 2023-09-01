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

# pylint: disable=redefined-outer-name
import os

import boto3
import pytest
from boto3.dynamodb.conditions import Key

TEST_CONFIG = {
    "base_url": f"{os.environ.get('BASE_URL')}v1/",
    "aws_region": os.environ.get("AWS_REGION", "ap-southeast-2"),
    "table_name": os.environ.get("TABLE_NAME", f"qgis-plugin-repo-{os.environ['RESOURCE_SUFFIX']}"),
    "secret": "",
    "hash": "",
    "plugin_id": os.environ.get("PLUGIN_ID", "PqvtapSnDMxnMqCh"),
    "plugin_metadata": """[general]
    name=test plugin
    icon=icon.png
    email=test@linz.govt.nz
    author=Yossarian
    description=Plugin for testing the repository
    version=0.1
    experimental=True
    about=this is a test
    repository=github/test
    qgisMinimumVersion=4.0.0
    qgisMaximumVersion=5.0.0""",
}


class Session:
    def __init__(self):
        self.session_vars = {}


@pytest.fixture(name="config_fixture")
def system_tests():
    """
    Return test config parameters
    """

    return TEST_CONFIG


@pytest.fixture(name="dynamodb_client_fixture")
def dynamodb_client():
    yield boto3.client(
        "dynamodb",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        region_name="ap-southeast-2",
    )


def clean_test_plugin():
    """
    Clean test database entries to allow next test to run
    """

    dynamodb = boto3.resource(
        "dynamodb",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
    )

    table = dynamodb.Table(TEST_CONFIG["table_name"])
    response = table.query(KeyConditionExpression=Key("id").eq(TEST_CONFIG["plugin_id"]))

    for item in response["Items"]:
        response = table.delete_item(Key={"id": item["id"], "item_version": item["item_version"]})


@pytest.fixture(autouse=True)
def cleanup():
    """
    Run post each test set/file
    """

    clean_test_plugin()
