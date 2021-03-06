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


def test_compatible_with_qgis_version_is_true():
    """
    QGIS version is greater than min plugin version but less than max.
    Should return true.
    """
    metadata = {"qgis_minimum_version": "3.0", "qgis_maximum_version": "3.9", "revisions": 2}
    result = plugin_xml.compatible_with_qgis_version(metadata, "3.2")
    assert result is True


def test_compatible_with_qgis_version_is_less_than():
    """
    QGIS version is less than min plugin version. Should return False
    """

    metadata = {"qgis_minimum_version": "3.2", "qgis_maximum_version": "3.99", "revisions": 2}
    result = plugin_xml.compatible_with_qgis_version(metadata, "3.0")
    assert result is False


def test_compatible_with_qgis_version_is_greater_than():
    """
    QGIS version is greater than max plugin version. Should return False
    """

    metadata = {"qgis_minimum_version": "3.2", "qgis_maximum_version": "3.99", "revisions": 2}
    result = plugin_xml.compatible_with_qgis_version(metadata, "4.0")
    assert result is False


def test_compatible_with_qgis_version_zero_revisions():
    """
    tets plugins with zero revisions are filtered prior to generating xml
    """

    metadata = {"qgis_minimum_version": "3.2", "qgis_maximum_version": "3.99", "revisions": 0}
    result = plugin_xml.compatible_with_qgis_version(metadata, "3.4")
    assert result is False


def test_compatible_with_qgis_version_default():
    """
    Test the default qgis version
    """

    metadata = {"qgis_minimum_version": "3.2", "qgis_maximum_version": "3.99", "revisions": 2}
    result = plugin_xml.compatible_with_qgis_version(metadata, "0.0.0")
    assert result is True


def test_generate_xml_body(mocker):
    """
    Test the xml generated for QGIS
    """

    mock_return = [
        {
            "id": "testPlugin",
            "version": "0.0.0",
            "revisions": 3,
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
        + "<revisions>3</revisions>"
        + "<created_at>2019-10-17T15:12:11.427110+00:00</created_at>"
        + "<qgis_minimum_version>3.0.0</qgis_minimum_version>"
        + "<file_name>testPlugin.0.0.0.zip</file_name>"
        + "<download_url>https://test.s3-ap-southeast-2.amazonaws.com/testPlugin.0.0.0.zip</download_url>"
        + "</pyqgis_plugin></plugins>"
    )
    repo_bucket_name = "test"
    aws_region = "ap-southeast-2"
    plugin_stage = "dev"

    result = plugin_xml.generate_xml_body(repo_bucket_name, aws_region, "0.0.0", plugin_stage)
    assert result == expected.encode()


def test_generate_xml_body_filter_revisions_eq_zero(mocker):
    """
    Test those items with revisions==0 are filtered out
    when the xml doc is generated for QGIS
    """

    mock_return = [
        {
            "id": "testPlugin",
            "version": "0.0.0",
            "revisions": 3,
            "name": "Test_Plugin",
            "created_at": "2019-10-17T15:12:11.427110+00:00",
            "file_name": "testPlugin.0.0.0.zip",
            "qgis_minimum_version": "3.0.0",
        },
        {
            "id": "testPluginRevZero",
            "revisions": 0,
            "version": "0.0.0",
            "name": "Test_Plugin",
            "created_at": "2019-10-17T15:12:11.427110+00:00",
            "file_name": "testPlugin.0.0.0.zip",
            "qgis_minimum_version": "3.0.0",
        },
    ]
    mocker.patch("src.plugin.metadata_model.MetadataModel.all_version_zeros", return_value=mock_return)

    expected = (
        "<plugins>"
        + '<pyqgis_plugin name="Test_Plugin" version="0.0.0">'
        + "<version>0.0.0</version>"
        + "<revisions>3</revisions>"
        + "<created_at>2019-10-17T15:12:11.427110+00:00</created_at>"
        + "<qgis_minimum_version>3.0.0</qgis_minimum_version>"
        + "<file_name>testPlugin.0.0.0.zip</file_name>"
        + "<download_url>https://test.s3-ap-southeast-2.amazonaws.com/testPlugin.0.0.0.zip</download_url>"
        + "</pyqgis_plugin></plugins>"
    )
    repo_bucket_name = "test"
    aws_region = "ap-southeast-2"
    plugin_stage = "dev"

    result = plugin_xml.generate_xml_body(repo_bucket_name, aws_region, "0.0.0", plugin_stage)
    assert result == expected.encode()
