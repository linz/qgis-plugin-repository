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


def test_get_access_token(mocker, api_fixture):
    """
    Test token is extracted from header
    """

    mocker.patch("werkzeug.local.LocalProxy.__getattr__", return_value={"authorization": "bearer 12345"})

    token = api_fixture.get_access_token()
    assert token == "12345"


def test_get_access_token_basic_token(mocker, api_fixture):
    """
    Test error raised is Auth is not baerer
    """

    mocker.patch("werkzeug.local.LocalProxy.__getattr__", return_value={"authorization": "basic 12345"})

    with pytest.raises(DataError) as error:
        api_fixture.get_access_token()
    assert "Invalid token" in str(error.value)


def test_get_access_token_no_auth_header(mocker, api_fixture):
    """
    Test error is raised is not auth header
    """
    mocker.patch(
        "werkzeug.local.LocalProxy.__getattr__",
        return_value={"environHeaders": "host: 127.0.0.1:5000", "user-agent": "curl/7.64.0", "accept": "*/*"},
    )

    with pytest.raises(DataError) as error:
        api_fixture.get_access_token()
    assert "Invalid token" in str(error.value)


if __name__ == "__main__":
    pytest.main()
