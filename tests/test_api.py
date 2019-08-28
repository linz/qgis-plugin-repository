import os
import zipfile
import pytest
from botocore.stub import Stubber, ANY
from src.plugin import api


@pytest.fixture()
def client():
    """
    Fixture yielding the flask test client
    """
    app = api.app
    app.testing = True
    client = app.test_client()
    yield client


@pytest.fixture(scope='module')
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
        'test_plugin': test_plugin,
        'test_plugin_no_md': test_plugin_no_md,
        'test_file_not_a_zipfile': test_file_not_a_zipfile,
        'response': response,
        'data': data}


@pytest.fixture(scope='module')
def plugin_zipfile(global_data):
    """
    Fixture yielding test plugin data
    """

    with zipfile.ZipFile(global_data['test_plugin'], "r") as plugin_zip:
        yield plugin_zip


@pytest.fixture(scope='module')
def plugin_zipfile_no_md(global_data):
    """
    Fixture yielding test plugin data
    """

    with zipfile.ZipFile(global_data['test_plugin_no_md'], "r") as plugin_zip_no_md:
        yield plugin_zip_no_md


@pytest.fixture()
def s3_stub():
    """
    Fixture yielding stubdeb s3 client
    """

    stubbed_client = api.s3_client
    with Stubber(stubbed_client) as stubber:
        yield stubber


def test_format_response():
    """
    Test to ensure correct response formatting
    """

    expected_result = {
        "description": "this is a test",
        "data": {"plugin_name": "test_plugin"},
    }

    result = api.format_response(
        http_code=200, description="this is a test", data={"plugin_name": "test_plugin"}
    )

    assert expected_result == result.get_json()
    assert result.status_code == 200


def test_get_metadata_path(plugin_zipfile):
    """
    Test that the method returns the metadata.txt path
    found within the plugin test data
    """

    result = api.get_metadata_path(plugin_zipfile)
    assert result == ["test_plugin/metadata.txt"]


def test_get_metadata_path_no_md(plugin_zipfile_no_md):
    """
    Test that the method returns an empty list when
    the plugin is missing the metadata.txt file
    """

    result = api.get_metadata_path(plugin_zipfile_no_md)
    assert result == []


def test_metadata_contents(plugin_zipfile):
    """
    Test the method extracts the metadata contents
    """

    result = api.metadata_contents(plugin_zipfile, "test_plugin/metadata.txt")
    assert result["general"]["name"] == "Testplugin"
    assert result["general"]["qgisMinimumVersion"] == "4.0"
    assert result["general"]["version"] == "0.1"
    assert result["general"]["description"] == "Plugin for testing the repository"


def test_upload_plugin_to_s3(s3_stub, global_data):
    """
    Test the upload_plugin_method returns
    the expected response on success
    """

    s3_stub.add_response(
        "put_object",
        expected_params={"Body": global_data['data'], "Bucket": "test_bucket", "Key": "test_plugin"},
        service_response=global_data['response'],
    )

    result = api.upload_plugin_to_s3(global_data['data'], "test_bucket", "test_plugin")

    assert result == (True, global_data['response'])


def test_upload_file_to_s3_error(s3_stub):
    """
    Test the upload_plugin_method returns
    the expected response on error
    """

    s3_stub.add_client_error(
        "put_object",
        expected_params={"Body": ANY, "Bucket": "test_bucket", "Key": "test_plugin"},
        service_error_code="404",
    )

    result = api.upload_plugin_to_s3("Durpa Durpa", "test_bucket", "test_plugin")
    assert result == (
        False,
        "An error occurred (404) when calling the PutObject operation: ",
    )


def test_upload_no_data(client):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits no data as
    part of the post
    """

    result = client.post("/plugin")
    assert result.status_code == 400
    assert result.get_json() == {"description": "No plugin file supplied", "data": {}}


def test_upload_no_stubmetadata(client, global_data):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits plugin
    data that contains no metadata.txt
    """

    with open(global_data['test_plugin_no_md'], "rb") as file_data:
        bytes_content = file_data.read()
    result = client.post("/plugin", data=bytes_content)
    assert result.status_code == 400
    assert result.get_json() == {"description": "metadata.txt not found", "data": {}}


def test_upload_not_a_zipfile(client, global_data):
    """
    Via the flask client hit the /plugin POST endpoint
    to test error catching when the user submits plugin
    data that is not a zipfile
    """

    result = client.post("/plugin", data=global_data['test_file_not_a_zipfile'])
    assert result.status_code == 400
    assert result.get_json() == {"description": "File must be a zipfile", "data": {}}


def test_upload_data(client, s3_stub, global_data):
    """
    When the users submits the correct plugin data
    test API responds indicating success.

    This test is at the integration level
    """

    with open(global_data['test_plugin'], "rb") as file_data:
        bytes_content = file_data.read()

    s3_stub.add_response(
        "put_object",
        expected_params={
            "Body": bytes_content,
            "Bucket": "qgis-plugin-repository",
            "Key": "Testplugin0.1",
        },
        service_response=global_data['response'],
    )

    result = client.post("/plugin", data=bytes_content)
    assert result.status_code == 201
    assert result.get_json() == {
        "description": "plugin uploaded",
        "data": {"pluginName": "Testplugin0.1"},
    }


if __name__ == "__main__":
    pytest.main()
