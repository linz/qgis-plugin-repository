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


def test_generate_xml_body(mocker):
    """
    Test the xml generated for QGIS
    """

    mock_return = [
        {
            "id": "test+plugin",
            "version": "0.0.0",
            "name": "Test_Plugin",
            "created_at": "2019-10-17T15:12:11.427110+00:00",
            "file_name": "1111-1111-1111-1111",
        }
    ]

    mocker.patch("src.plugin.metadata_model.MetadataModel.all_version_zeros", return_value=mock_return)

    expected = (
        "<plugins>"
        + '<pyqgis_plugin name="Test_Plugin" version="0.0.0">'
        + "<version>0.0.0</version>"
        + "<created_at>2019-10-17T15:12:11.427110+00:00</created_at>"
        + "<file_name>1111-1111-1111-1111</file_name>"
        + "<download_url>https://test.s3-ap-southeast-2.amazonaws.com/1111-1111-1111-1111</download_url>"
        + "</pyqgis_plugin></plugins>"
    )
    repo_bucket_name = "test"
    aws_region = "ap-southeast-2"

    result = plugin_xml.generate_xml_body(repo_bucket_name, aws_region)
    print(result)
    assert result == expected.encode()
