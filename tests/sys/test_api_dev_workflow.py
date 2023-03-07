"""
################################################################################
#
#  LINZ QGIS plugin repository,
#  Crown copyright (c) 2020, Land Information New Zealand on behalf of
#  the New Zealand Government.
#
#  This file is released under the MIT licence. See the LICENCE file found
#  in the top-level directory of this distribution for more information.
#
################################################################################

    Wrapper around api_workflow_tests to test development plugin's
    API workflow

"""


import pytest

from tests.sys import api_workflow_tests


def test_post_dev_plugin(config_fixture):
    api_workflow_tests.test_post_plugin(config_fixture, "dev")


def test_get_dev_plugins(config_fixture):
    api_workflow_tests.test_get_plugins(config_fixture, "dev")


def test_revision_dev_plugin(config_fixture):
    api_workflow_tests.test_revision_plugin(config_fixture, "dev")


def test_retire_dev_plugin(config_fixture):
    api_workflow_tests.test_retire_plugin(config_fixture, "dev")


def test_revive_dev_plugin(config_fixture):
    api_workflow_tests.test_revive_plugin(config_fixture, "dev")


def test_plugin_dev_xml(config_fixture):
    api_workflow_tests.test_plugin_xml(config_fixture, "dev")


def test_download_dev_plugin(config_fixture):
    api_workflow_tests.test_download_plugin(config_fixture, "dev")
