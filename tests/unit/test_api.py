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


if __name__ == "__main__":
    pytest.main()
