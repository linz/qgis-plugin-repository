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

    For parsing plugin metadata

"""


import configparser
import os
import re
from io import StringIO

from src.plugin.error import DataError


def metadata_path(plugin_zipfile):
    """
    Get reference to metadata.txt within zipfile.
    :param plugin_zipfile: Zipfile obj representing the plugin
    :type plugin_zipfile: zipfile.ZipFile
    :returns: metadata.txt path
    :rtype: str
    """

    # Get Metadata.txt path
    plugin_files = plugin_zipfile.namelist()
    path = [i for i in plugin_files if re.search(r"^[^/]*/metadata\.txt$", i)]
    if not path:
        raise DataError(400, "No metadata.txt file found in plugin directory")
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

    # Get root dir
    filelist = plugin_zipfile.filelist
    plugin_root = set(path.filename.split(os.sep)[0] for path in filelist)
    if len(plugin_root) > 1:
        raise DataError(400, "Multiple directories exists at the root level. There should only be one")
    if not plugin_root:
        raise DataError(400, "The plugin has no root directory. One must exist")
    plugin_root = next(iter(plugin_root))
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

    return config_parser
