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


def test_format_error(api_fixture):
    """
    Test to ensure correct response formatting
    """

    app = api_fixture.app
    app_context = app.app_context()
    app_context.push()

    result = api_fixture.format_error("This is a error", 400)

    assert result[0].json == {"message": "This is a error"}
    assert result[1] == 400


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


def test_validate_user_data_no_data(api_fixture):
    """
    If not data return error
    """
    with pytest.raises(DataError) as error:
        api_fixture.validate_user_data(None)
    assert "No plugin file supplied" in str(error.value)


def test_validate_user_data_not_zip(api_fixture):
    """
    If not data return error
    """

    with pytest.raises(DataError) as error:
        api_fixture.validate_user_data(b"0011010101010")
    assert "Plugin file supplied not a Zipfile" in str(error.value)


def test_validate_user_data_is_zip(api_fixture):
    """
    No errors should be returned is a zipfile is supplied
    """

    api_fixture.validate_user_data(b"PK\x05\x06\x00\x00\x00\x00\x04\x00\x04\x00\x8e\x01\x00\x00\xa2\t\x00\x00\x00\x00")


if __name__ == "__main__":
    pytest.main()
