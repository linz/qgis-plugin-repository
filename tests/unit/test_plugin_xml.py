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

from src.plugin import plugin_xml


def test_generate_download_url():
    """
    Test the generation of the download url
    """

    repo_bucket_name = "test"
    aws_region = "ap-southeast-2"
    plugin_id = "e8363fdd-450a-4fc2-bb9e-16e9b80a7c85"
    result = plugin_xml.generate_download_url(repo_bucket_name, aws_region, plugin_id)
    assert result == "https://test.s3-ap-southeast-2.amazonaws.com/e8363fdd-450a-4fc2-bb9e-16e9b80a7c85"


def test_new_xml_element():
    """
    Test the creation of new xml elements
    """

    parameter = "Name"
    value = "Test"
    result = plugin_xml.new_xml_element(parameter, value)
    assert result.tag == "Name"
    assert result.text == "Test"


def test_greater_than_min_qgis_version_is_greater():
    """
    Test True is returned when plugin metadata qgis_minimum_version
    is greater than user defined min version
    """
    metadata = {"name": "a_plugin", "qgis_minimum_version": "9.9.9"}
    result = plugin_xml.greater_than_min_qgis_version(metadata, "9.9.8")
    assert result is True


def test_greater_than_min_qgis_version_is_less():
    """
    Test False is returned when plugin metadata qgis_minimum_version
    is less than user defined min version
    """

    metadata = {"name": "a_plugin", "qgis_minimum_version": "1.9.9"}
    result = plugin_xml.greater_than_min_qgis_version(metadata, "9.9.8")
    assert result is False


def test_greater_than_min_qgis_version_is_equall():
    """
    Test True is returned when plugin metadata qgis_minimum_version
    is equall to user defined min version
    """

    metadata = {"name": "a_plugin", "qgis_minimum_version": "9.0.0"}
    result = plugin_xml.greater_than_min_qgis_version(metadata, "9.0.0")
    assert result is True


def test_generate_xml_body(mocker):
    """
    Test the xml generated for QGIS
    """

    mock_return = [
        {
            "id": "testPlugin",
            "version": "0.0.0",
            "name": "Test_Plugin",
            "created_at": "2019-10-17T15:12:11.427110+00:00",
            "file_name": "testPlugin.0.0.0.zip",
            "qgis_minimum_version": "3.0.0",
        }
    ]

    mocker.patch("src.plugin.metadata_model.MetadataModel.all_version_zeros", return_value=mock_return)

    expected = (
        "<plugins>"
        + '<pyqgis_plugin name="Test_Plugin" version="0.0.0">'
        + "<version>0.0.0</version>"
        + "<created_at>2019-10-17T15:12:11.427110+00:00</created_at>"
        + "<qgis_minimum_version>3.0.0</qgis_minimum_version>"
        + "<file_name>testPlugin.0.0.0.zip</file_name>"
        + "<download_url>https://test.s3-ap-southeast-2.amazonaws.com/testPlugin.0.0.0.zip</download_url>"
        + "</pyqgis_plugin></plugins>"
    )
    repo_bucket_name = "test"
    aws_region = "ap-southeast-2"

    result = plugin_xml.generate_xml_body(repo_bucket_name, aws_region, "0.0.0")
    assert result == expected.encode()
