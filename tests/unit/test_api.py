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
from src.plugin.api import get_access_token
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


def test_get_access_token():
    """
    Test token is extracted from header
    """

    headers = {
        "EnvironHeaders": "Host: 127.0.0.1:5000",
        "User-Agent": "curl/7.64.0",
        "Accept": "*/*",
        "Authorization": "Bearer 12345",
    }
    token = get_access_token(headers)
    assert token == "12345"


def test_get_access_token_basic_token():
    """
    Test error raised is Auth is not baerer
    """

    headers = {
        "EnvironHeaders": "Host: 127.0.0.1:5000",
        "User-Agent": "curl/7.64.0",
        "Accept": "*/*",
        "Authorization": "Basic 12345",
    }
    with pytest.raises(DataError) as error:
        get_access_token(headers)
    assert "Invalid token" in str(error.value)


def test_get_access_token_no_auth_header():
    """
    Test error is raised is not auth header
    """

    headers = {"EnvironHeaders": "Host: 127.0.0.1:5000", "User-Agent": "curl/7.64.0", "Accept": "*/*"}
    with pytest.raises(DataError) as error:
        get_access_token(headers)
    assert "Invalid token" in str(error.value)


if __name__ == "__main__":
    pytest.main()
