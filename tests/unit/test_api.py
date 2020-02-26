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
from src.plugin.error import DataError


def test_format_response(api_fixture):
    """
    Test to ensure correct response formatting
    """

    expected_result = {"plugin_name": "test_plugin"}

    app = api_fixture.app
    app_context = app.app_context()
    app_context.push()

    result = api_fixture.format_response({"plugin_name": "test_plugin"}, 201)

    assert result[0].json == expected_result
    assert result[1] == 201


def test_get_access_token(api_fixture):
    """
    Test token is extracted from header
    """

    token = api_fixture.get_access_token({"authorization": "bearer 12345"})
    assert token == "12345"


def test_get_access_token_basic_token(api_fixture):
    """
    Test error raised is Auth is not baerer
    """

    with pytest.raises(DataError) as error:
        api_fixture.get_access_token({"authorization": "basic 12345"})
    assert "Invalid token" in str(error.value)


def test_get_access_token_no_auth_header(api_fixture):
    """
    Test error is raised is not auth header
    """

    with pytest.raises(DataError) as error:
        api_fixture.get_access_token({"environHeaders": "host: 127.0.0.1:5000", "user-agent": "curl/7.64.0", "accept": "*/*"})
    assert "Invalid token" in str(error.value)


def test_validate_qgis_version_pass():
    """
    Test correct software version string formats pass validation
    """
    versions = ["0.0", "0.0.0", "2.0", "3.0", "3.100", "3.10.1", "3.10.99", "10.0", "10.1", "10.10.10"]
    for version in versions:
        api.validate_qgis_version(version)


def test_validate_qgis_version_fail():
    """
    Test invalid software version string formats fail validation
    """

    versions = ["2", "two", "4.4.4.4", "3.10.a1"]
    for version in versions:
        with pytest.raises(DataError) as error:
            api.validate_qgis_version(version)
    assert "Invalid QGIS version" in str(error.value)


if __name__ == "__main__":
    pytest.main()
