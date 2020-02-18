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

import tempfile
import zipfile
import configparser
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


def test_remove_no_values():
    """
    Test the removal of keys with empty strings from
    config parser
    """

    config = configparser.ConfigParser()
    config.add_section("general")
    config["general"]["name"] = "plugin"
    config["general"]["qgisMinimumVersion"] = "4.0"
    config["general"]["version"] = "0.1"
    config["general"]["tags"] = ""

    # Check the key is in the config
    assert "tags" in config["general"]

    # run method to remove key
    plugin_parser.metadata_remove_no_values(config)
    assert "name" in config["general"]
    assert "qgisMinimumVersion" in config["general"]
    assert "qgisMinimumVersion" in config["general"]

    # key should no longer be present in config
    assert "tags" not in config["general"]
