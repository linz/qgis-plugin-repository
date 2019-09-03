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

import os
import zipfile
import pytest
from botocore.stub import Stubber
from src.plugin import api


@pytest.fixture(name="client_fixture")
def client():
    """
    Fixture yielding the flask test client
    """
    app = api.app
    app.testing = True
    yield app.test_client()


@pytest.fixture(name="global_data_fixture", scope="module")
def global_data():
    """
    Fixture yielding variables to individual tests
    """

    test_dir = os.path.dirname(os.path.realpath(__file__))
    test_data_dir = os.path.join(test_dir + "/data")
    test_plugin = os.path.join(test_data_dir + "/test_plugin.zip")
    test_plugin_no_md = os.path.join(test_data_dir + "/test_plugin_no_metadata.zip")
    test_file_not_a_zipfile = os.path.join(test_data_dir + "/not_a_zipfile.txt")
    response = {
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
    }
    data = """
        01111001 01101111 01110101 00100000 01101000 01100001
        01110110 01100101 00100000 01110100 01101111 01101111
        00100000 01101101 01110101 01100011 01101000 00100000
        01110100 01101001 01101101 01100101 00100000 01101111
        01101110 00100000 01111001 01101111 01110101 01110010
        00100000 01101000 01100001 01101110 01100100 01110011
        """

    return {
        "test_plugin": test_plugin,
        "test_plugin_no_md": test_plugin_no_md,
        "test_file_not_a_zipfile": test_file_not_a_zipfile,
        "response": response,
        "data": data,
    }


@pytest.fixture(name="plugin_zipfile_fixture", scope="module")
def plugin_zipfile(global_data_fixture):
    """
    Fixture yielding test plugin data
    """

    with zipfile.ZipFile(global_data_fixture["test_plugin"], "r") as plugin_zip:
        yield plugin_zip


@pytest.fixture(name="plugin_zipfile_no_md_fixture", scope="module")
def plugin_zipfile_no_md(global_data_fixture):
    """
    Fixture yielding test plugin data
    """

    with zipfile.ZipFile(global_data_fixture["test_plugin_no_md"], "r") as plugin_zip_no_md:
        yield plugin_zip_no_md


@pytest.fixture(name="s3_stub_fixture")
def s3_stub():
    """
    Fixture yielding stubdeb s3 client
    """

    stubbed_client = api.s3_client
    with Stubber(stubbed_client) as stubber:
        yield stubber
