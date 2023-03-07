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

from datetime import datetime
import pytest

from src.plugin import api


@pytest.fixture(name="api_fixture")
def api_fixture(monkeypatch):
    """
    Must monkey patch envi vars before importing the api module
    """

    monkeypatch.setenv("REPO_BUCKET_NAME", "dummy")
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "dummy")
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", "dummy")
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_VERSION", "dummy")
    monkeypatch.setenv("AWS_LAMBDA_LOG_STREAM_NAME", "dummy")
    monkeypatch.setenv("AWS_REGION", "dummy")

    return api


@pytest.fixture(name="client_fixture")
def client(api_fixture):
    """
    Fixture yielding the flask test client
    """

    app = api_fixture.app
    app.testing = True

    yield app.test_client()


@pytest.fixture(name="now_fixture")
def datetime_now():
    """
    Fixture yielding static time and date for mocks
    """

    now = datetime.now()
    yield now


@pytest.fixture(name="api_version")
def api_version():
    """
    Fixture yielding static time and date for mocks
    """

    return "v1"
