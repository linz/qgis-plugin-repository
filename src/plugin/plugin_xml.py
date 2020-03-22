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


import xml.etree.ElementTree as ET

# pylint is unable to import distutils.version under virtualenv (affects travis)
# pylint: disable=no-name-in-module,import-error
from distutils.version import StrictVersion
from src.plugin.metadata_model import MetadataModel


def generate_download_url(repo_bucket_name, aws_region, plugin_id):
    """
    Returns path to plugin download
    :param repo_bucket_name: s3 bucket name
    :type repo_bucket_name: string
    :param aws_region:  aws_region
    :type aws_region: string
    :param plugin_id: plugin_id
    :type plugin_id: string
    :returns: path to plugin download
    :rtype: string
    """

    return "https://{0}.s3-{1}.amazonaws.com/{2}".format(repo_bucket_name, aws_region, plugin_id)


def new_xml_element(parameter, value):
    """
    Build new xml element
    :param parameter: New xml element parameter
    :type parameter: string
    :param value:  New xml element value
    :type value: string

    :returns: ElementTree Element
    :rtype: xml.etree.ElementTree.Element
    """

    new_element = ET.Element(parameter)
    new_element.text = str(value)
    return new_element


def compatible_with_qgis_version(metadata, qgis_version):
    """
    Test if plugin's  and max version are compatible with the QGIS version.
    :param metadata: Dictionary of plugin metadata
    :type metadata: dictionary
    :param min_version: User defined min qgis version
    :type min_version: string
    :returns: True if compatible
    :rtype: boolean
    """

    if metadata["revisions"] == 0:
        return False
    if qgis_version == "0.0.0":
        return True
    return StrictVersion(metadata["qgis_minimum_version"]) <= StrictVersion(qgis_version) and StrictVersion(
        qgis_version
    ) <= StrictVersion(metadata["qgis_maximum_version"])


def generate_xml_body(repo_bucket_name, aws_region, qgis_version, plugin_stage):
    """
    Generate XML describing plugin store
    from dynamodb plugin metadata db
    :param repo_bucket_name: s3 bucket name
    :type repo_bucket_name: string
    :param aws_region:  aws_region
    :type aws_region: string
    :returns: string representation of plugin xml
    :rtype: string
    """

    current_plugins = filter(
        lambda item: compatible_with_qgis_version(item, qgis_version), MetadataModel.all_version_zeros(plugin_stage)
    )
    root = ET.Element("plugins")
    for plugin in current_plugins:
        if not plugin["revisions"]:
            continue
        current_group = ET.SubElement(root, "pyqgis_plugin", {"name": plugin["name"], "version": plugin["version"]})
        for key, value in plugin.items():
            if key not in ("file_name", "name", "id", "category", "email", "item_version", "stage"):
                new_element = new_xml_element(key, value)
                current_group.append(new_element)
        new_element = new_xml_element("file_name", f"{plugin['id']}.{plugin['version']}.zip")
        current_group.append(new_element)
        download_url = generate_download_url(repo_bucket_name, aws_region, plugin["file_name"])
        new_element = new_xml_element("download_url", download_url)
        current_group.append(new_element)
    return ET.tostring(root)
