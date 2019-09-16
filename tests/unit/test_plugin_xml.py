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

import datetime
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

    mock_return = {
        "88f530e5-8914-4bf8-9351-f351e6b0e8fb": {
            "id": "88f530e5-8914-4bf8-9351-f351e6b0e8fb",
            "version": "0.0.0",
            "name": "Test_Plugin",
            "created_at": datetime.datetime(2019, 9, 16, 2, 4, 12, 590806, tzinfo=datetime.timezone.utc),
        }
    }

    mocker.patch("src.plugin.metadata_model.MetadataModel.json_dump_model_current", return_value=mock_return)

    expected = (
        "<plugins>"
        + '<pyqgis_plugin name="Test_Plugin" version="0.0.0"><version>0.0.0'
        + "</version><created_at>2019-09-16 02:04:12.590806+00:00</created_at>"
        + "<download_url>https://test.s3-ap-southeast-2.amazonaws.com/88f530e5-8914-4bf8-9351-f351e6b0e8fb</download_url>"
        + "</pyqgis_plugin>"
        + "</plugins>"
    )

    repo_bucket_name = "test"
    aws_region = "ap-southeast-2"

    result = plugin_xml.generate_xml_body(repo_bucket_name, aws_region)
    assert result == expected.encode()
