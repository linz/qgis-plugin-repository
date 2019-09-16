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

    Flask API for managing QGIS Plugins in S3

"""

import os
import re
import json
import logging
import zipfile
import configparser
import uuid
from io import BytesIO, StringIO
import xml.etree.ElementTree as ET
from flask import Flask, request
import boto3
from src.plugin.metadata_model import MetadataModel


app = Flask(__name__)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Repository bucket name
repo_bucket_name = os.environ["REPO_BUCKET_NAME"]

# AWS region
aws_region = os.environ.get("REGION", None)

# Boto S3 client
s3_client = boto3.client("s3")


def format_error(message, http_code):
    """"
    format error responses

    :param message: API response message to be returned as part of the API response
    :type message: int
    :param http_code: http_code to return as part of the API response
    :type http_code: str
    :returns: API error response
    :rtype: flask.wrappers.Response
    """

    response_body = {"message": message}
    response = app.response_class(response=json.dumps(response_body), status=http_code, mimetype="application/json")
    return response


def format_response(data, http_code):
    """
    format the http response

    :param data: Data to return as part of the API response
    :type data: Dict
    :param http_code: http_code to return as part of the API response
    :type http_code: str
    :returns: API error response
    :rtype: flask.wrappers.Response
    """

    # once metadata handling is delivered, this will always return standard plugin metadata
    response = app.response_class(response=json.dumps(data), status=http_code, mimetype="application/json")
    return response


def get_metadata_path(plugin_zipfile):
    """
    Returns a list of possible metadata.txt matches.
    The regex applied to the zipfles namelist only matches
    one dir deep - therefore it will either return an list with
    one item (path to metadata.txt) else an empty list. If its
    is an empty list that is returned, the metadata.txt was not found

    :param plugin_zipfile: Zipfile obj representing the plugin
    :type plugin_zipfile: zipfile.ZipFile
    :returns: List of metadata path
    :rtype: list
    """

    plugin_files = plugin_zipfile.namelist()
    metadata_path = [i for i in plugin_files if re.search(r"^\w*\/{1}metadata.txt", i)]

    logging.info("Plugin metadata path: %s", metadata_path)
    return metadata_path


def get_zipfile_root_dir(plugin_zipfile):
    """
    The plugin file must have a root directory. When unziped
    QGIS uses this directory name to refer to the installation.
    :param plugin_zipfile: Zipfile obj representing the plugin
    :type plugin_zipfile: zipfile.ZipFile
    :returns: tuple==(<error message>, <root dir name>)
    :rtype: tuple
    """

    error = None

    filelist = plugin_zipfile.filelist
    plugin_root = set(path.filename.split(os.sep)[0] for path in filelist)

    if len(plugin_root) > 1:
        error = "plugin zipfile has multiple folders at root level"
        logging.error("plugin zipfile has multiple folders at root level")
        return error, None
    if not plugin_root:
        error = "plugin zipfile has no root directory"
        logging.error("plugin zipfile has no root directory")
        return error, None
    plugin_root = next(iter(plugin_root))
    logging.info("plugin_root: %s", plugin_root)
    return (None, plugin_root)


def metadata_contents(plugin_zipfile, metadata_path):
    """
    Return metadata.txt contents that is stored in
    the plugin .zip file

    :param plugin_zipfile: Zipfile obj representing the plugin
    :type plugin_zipfile: zipfile.ZipFile
    :param metadata_path: Path in <plugin>.zip to metadata.txt file
    :type metadata_path: str
    :returns: ConfigParser representation of metadata
    :rtype: configparser.ConfigParser
    """

    metadata = plugin_zipfile.open(metadata_path)
    metadata = str(metadata.read(), "utf-8")
    config_parser = configparser.ConfigParser()
    config_parser.read_file(StringIO(metadata))

    logging.info("Plugin metadata: %s", config_parser)
    return config_parser


def update_metadata_db(metadata, plugin_id, plugin_file_name):
    """
    Update dynamodb metadata store for uploaded plugin

    :param metadata: ConfigParser representation of metadata.txt
    :type metadata: configparser.ConfigParser
    :returns: tuple (<error>, <plugin_id>).
              if successful error == None
              plugin_id == <plugin_name>+<plugin_version>
    :rtype: tuple
    """

    general_metadata = metadata["general"]
    plugin = MetadataModel(
        id=plugin_id,  # partition_key
        name=general_metadata.get("name", None),
        version=general_metadata.get("version", None),
        qgis_minimum_version=general_metadata.get("qgisMinimumVersion", None),
        qgis_maximum_version=general_metadata.get("qgisMaximumVersion", None),
        description=general_metadata.get("description", None),
        about=general_metadata.get("about", None),
        author_name=general_metadata.get("author", None),
        email=general_metadata.get("email", None),
        changelog=general_metadata.get("changelog", None),
        experimental=general_metadata.get("experimental", None),
        deprecated=general_metadata.get("deprecated", None),
        tags=general_metadata.get("tags", None),
        homepage=general_metadata.get("homepage", None),
        repository=general_metadata.get("repository", None),
        tracker=general_metadata.get("tracker", None),
        icon=general_metadata.get("icon", None),
        category=general_metadata.get("category", None),
        file_name=plugin_file_name,
    )

    try:
        plugin.save()
        return None
    except ValueError as error:
        logging.error("ValueError: %s", error)
        return ("ValueError: {0}").format(error)


def get_most_current_plugins_metadata():
    """
    The metadata database retains all iterations of the plugin unless
    the record is explicitly deleted by the user. This method only
    returns distinct plugin_id with the most recent created date for each.

    :returns: Dict of distinct plugins
    :rtype: Dict
    """

    most_current = {}
    for item in MetadataModel.scan():
        if item.id in most_current:
            if item.created_at > most_current[item.id]["created_at"]:
                most_current[item.id] = item.attribute_values
        else:
            most_current[item.id] = item.attribute_values
    return most_current


def generate_download_url(plugin_id):
    """
    Returns path to plugin download

    :param plugin_id: plugin_id
    :type plugin_id: string
    :returns: path to plugin download
    :rtype: string
    """

    download_url = ("https://{0}.s3-{1}.amazonaws.com/{2}".format(repo_bucket_name, aws_region, plugin_id),)
    return download_url


def new_xml_element(parameter, value):
    """
    Return build new xml element
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


def generate_metadata_xml():
    """
    Generate XML describing plugin store
    from dynamodb plugin metadata store

    :returns: string representation of plugin xml
    :rtype: string
    """

    current_plugins = get_most_current_plugins_metadata()

    root = ET.Element("plugins")
    for plugin in current_plugins.values():
        current_group = ET.SubElement(root, "pyqgis_plugin", {"name": plugin["name"], "version": plugin["version"]})
        for key, value in plugin.items():
            if key not in ("name", "id", "plugin_id", "changelog", "category", "email"):
                new_element = new_xml_element(key, value)
                current_group.append(new_element)
        download_url = generate_download_url(plugin["id"])
        new_element = new_xml_element("download_url", download_url)
        current_group.append(new_element)
    return ET.tostring(root)


def put_to_s3(data, bucket, object_name, content_disposition=None):
    """
    Upload plugin file to S3 plugin repository bucket

    :param data: Object data
    :type data: binary
    :param bucket: bucket name
    :type bucket: str
    """

    s3_client.put_object(Body=data, Bucket=bucket, Key=object_name, ContentDisposition=content_disposition)


def validate_user_data(data):
    """
    ensure data was submitted by the user and it
    is a zipfile

    :param data: Object data
    :type data: binary
    """

    # Check data was posted by the user
    error = None
    if not data:
        logging.error("Data Error: No plugin file supplied")
        error = "No plugin file supplied"
        return error

    # Test the file is a zipfile
    if not zipfile.is_zipfile(BytesIO(data)):
        logging.error("Data Error: Plugin file supplied not a Zipfile")
        error = "File must be a zipfile"
        return error

    return error


@app.route("/plugins", methods=["POST"])
def upload():
    """
    End point for processing data POSTed by the user

    :returns: flask response
    :rtype: flask.wrappers.Response
    """

    try:
        post_data = request.get_data()
        error = validate_user_data(post_data)
        if error:
            return format_error(error, 400)

        # Extract plugin metadata
        plugin_zipfile = zipfile.ZipFile(BytesIO(post_data), "r", zipfile.ZIP_DEFLATED, False)
        metadata_path = get_metadata_path(plugin_zipfile)
        if not metadata_path:
            logging.error("Data Error: metadata.txt not found")
            return format_error("metadata.txt not found", 400)
        metadata_path = metadata_path[0]
        metadata = metadata_contents(plugin_zipfile, metadata_path)

        # Upload plugin to s3 bucket
        error, content_disposition = get_zipfile_root_dir(plugin_zipfile)
        if error:
            return format_error(error, 400)
        plugin_id = str(uuid.uuid4())
        put_to_s3(post_data, repo_bucket_name, plugin_id, content_disposition)
        logging.info("Plugin Upload: %s", plugin_id)

        # Update metadata database
        error = update_metadata_db(metadata, plugin_id, content_disposition)
        if error:
            return format_error(error, 400)

        return format_response({"plugin_id": plugin_id}, 201)

    # pylint: disable=W0703
    except Exception as error:
        logging.error("Error: %s", error)
        return format_error("Upload failed :See logs", 500)


@app.route("/plugins", methods=["GET"])
def get_plugins():
    """"
    Get xml describing current plugins
    """

    # Upload plugin xml
    xml = generate_metadata_xml()
    logging.info("plugins.xml updated")
    return app.response_class(response=xml, status=200, mimetype="text/xml")


if __name__ == "__main__":
    app.run(debug=True)
