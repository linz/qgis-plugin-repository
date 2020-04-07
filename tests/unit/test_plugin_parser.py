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

import tempfile
import zipfile
import pytest
from src.plugin.error import DataError
from src.plugin import plugin_parser


def test_metadata_path():
    """
    Test that the method returns the metadata.txt path
    found within the plugin test data
    """
    with tempfile.SpooledTemporaryFile() as tmp:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("plugin/metadata.txt", "[general]\nname=Testplugin\nicon=icon.png")
            archive.writestr("plugin/testplugin.py", "print(hello word)")
            result = plugin_parser.metadata_path(archive)
    assert result == "plugin/metadata.txt"


def test_metadata_path_no_md():
    """
    Test that the method returns an empty list when
    the plugin is missing the metadata.txt file
    """

    with tempfile.SpooledTemporaryFile() as tmp:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("plugin/testplugin.py", "print(hello word)")
            with pytest.raises(DataError) as error:
                plugin_parser.metadata_path(archive)
    assert "No metadata.txt file found in plugin directory" in str(error.value)


def test_get_zipfile_root_dir():
    """
    Test the extraction of the zipfile root dir
    """

    with tempfile.SpooledTemporaryFile() as tmp:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("plugin/testplugin.py", "print(hello word)")
            result = plugin_parser.zipfile_root_dir(archive)
    assert result == ("plugin")


def test_get_zipfile_many_root_dir():
    """
    Test the extraction of the zipfile root dir
    """

    with tempfile.SpooledTemporaryFile() as tmp:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("plugin/testplugin.py", "print(hello word)")
            archive.writestr("stuffnthings/testplugin.py", "print(hello word)")
            with pytest.raises(DataError) as error:
                plugin_parser.zipfile_root_dir(archive)
    assert "Multiple directories exists at the root level. There should only be one" in str(error.value)


def test_metadata_contents():
    """
    Test the method extracts the metadata contents
    """
    with tempfile.TemporaryFile() as tmp:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("plugin/metadata.txt", "[general]\nname=plugin\nqgisMinimumVersion=4.0\nversion=0.1")
            archive.writestr("plugin/testplugin.py", "print(hello word)")
            result = plugin_parser.metadata_contents(archive, "plugin/metadata.txt")
    assert result["general"]["name"] == "plugin"
    assert result["general"]["qgisMinimumVersion"] == "4.0"
    assert result["general"]["version"] == "0.1"
