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

    Wrapper around api_workflow_tests to test production plugin's
    API workflow

"""

from . import api_workflow_tests


def test_post_prd_plugin(config_fixture):
    api_workflow_tests.test_post_plugin(config_fixture)


def test_get_prd_plugins(config_fixture):
    api_workflow_tests.test_get_plugins(config_fixture)


def test_revision_prd_plugin(config_fixture):
    api_workflow_tests.test_revision_plugin(config_fixture)


def test_retire_prd_plugin(config_fixture):
    api_workflow_tests.test_retire_plugin(config_fixture)


def test_revive_prd_plugin(config_fixture):
    api_workflow_tests.test_revive_plugin(config_fixture)


def test_plugin_prd_xml(config_fixture):
    api_workflow_tests.test_plugin_xml(config_fixture)


def test_download_prd_plugin(config_fixture):
    api_workflow_tests.test_download_plugin(config_fixture)
