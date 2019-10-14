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

    For parsing plugin metadata

"""


import re
import configparser
from io import StringIO
import logging
import os
from src.plugin.error import DataError


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def metadata_path(plugin_zipfile):
    """
    Get reference to metadata.txt within zipfile.

    :param plugin_zipfile: Zipfile obj representing the plugin
    :type plugin_zipfile: zipfile.ZipFile
    :returns: metadata.txt path
    :rtype: str
    """

    # Possible errors
    errors = {"missing_metadata": "No metadata.txt file found in plugin directory"}

    # Get Metadata.txt path
    plugin_files = plugin_zipfile.namelist()
    path = [i for i in plugin_files if re.search(r"^[^/]*/metadata\.txt$", i)]
    if not path:
        raise DataError(errors["missing_metadata"])
    logging.info("Metadata path: %s", path[0])
    return path[0]


def zipfile_root_dir(plugin_zipfile):
    """
    The plugin file must have a root directory. When unziped
    QGIS uses this directory name to refer to the installation.
    :param plugin_zipfile: Zipfile obj representing the plugin
    :type plugin_zipfile: zipfile.ZipFile
    :returns:  root dir name
    :rtype: str
    """

    # Possible errors
    errors = {
        "multiple_root_dirs": "Multiple directories exists at the root level. There should only be one",
        "missing_root_dir": "The plugin has no root directory. One must exist",
    }

    # Get root dir
    filelist = plugin_zipfile.filelist
    plugin_root = set(path.filename.split(os.sep)[0] for path in filelist)
    if len(plugin_root) > 1:
        raise DataError(errors["multiple_root_dirs"])
    if not plugin_root:
        raise DataError(errors["missing_root_dir"])
    plugin_root = next(iter(plugin_root))
    logging.info("plugin_root: %s", plugin_root)
    return plugin_root


def metadata_contents(plugin_zipfile, metadata):
    """
    Return metadata.txt contents
    :param plugin_zipfile: Zipfile obj representing the plugin
    :type plugin_zipfile: zipfile.ZipFile
    :param metadata_path: Path in <plugin>.zip to metadata.txt file
    :type metadata_path: str
    :returns: ConfigParser representation of metadata
    :rtype: configparser.ConfigParser
    """

    metadata = plugin_zipfile.open(metadata)
    metadata = str(metadata.read(), "utf-8")
    config_parser = configparser.ConfigParser()
    config_parser.read_file(StringIO(metadata))

    logging.info("Plugin metadata: %s", config_parser)
    return config_parser
