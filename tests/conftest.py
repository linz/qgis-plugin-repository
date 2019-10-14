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


import pytest


@pytest.fixture(name="api_fixture")
def api(monkeypatch):
    """
    Must monkey patch envi vars before importing the api module
    """

    monkeypatch.setenv("REPO_BUCKET_NAME", "dummy")
    from src.plugin import api

    return api


@pytest.fixture(name="client_fixture")
def client(api_fixture):
    """
    Fixture yielding the flask test client
    """

    app = api_fixture.app
    app.testing = True
    yield app.test_client()
