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

    Flask API for managing the storage and retrieval QGIS Plugins in S3

"""
# pylint: disable=W0703


import os
import logging
import zipfile
import uuid
from io import BytesIO
from datetime import datetime
from flask import Flask, request, jsonify
from src.plugin import plugin_parser
from src.plugin import aws
from src.plugin import plugin_xml
from src.plugin.metadata_model import MetadataModel
from src.plugin.error import DataError


app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Repository bucket name
# repo_bucket_name = os.environ["REPO_BUCKET_NAME"]
repo_bucket_name = os.environ.get("REPO_BUCKET_NAME")

# AWS region
aws_region = os.environ.get("AWS_REGION", None)


def format_error(message, http_code):
    """"
    Format API error responses

    :param message: Message to be returned as part of the API response
    :type message: str
    :param http_code: API response code to be return
    :type http_code: int
    :returns: API response
    :rtype: flask.wrappers.Response
    """

    response_body = {"message": message}
    logging.info("Response Message: %s", message)
    response = jsonify(response_body), http_code
    return response


def format_response(data, http_code):
    """
    Format the API response

    :param data: Body of API response
    :type data: Dict
    :param http_code: API response code to be return
    :type http_code: int
    :returns: API response
    :rtype: flask.wrappers.Response
    """

    response = jsonify(data), http_code
    logging.info("Response Data: %s", str(data))
    return response


def validate_user_data(data):
    """
    Basic validation of data PUT to the API
    :param data: Object data
    :type data: binary
    :returns: Return description of data error
    :rtype: str
    """

    # Possible errors
    errors = {"plugin_missing": "No plugin file supplied", "not_zipfile": "Plugin file supplied not a Zipfile"}

    # Check data was posted by the user
    if not data:
        raise DataError(errors["plugin_missing"])

    # Test the file is a zipfile
    if not zipfile.is_zipfile(BytesIO(data)):
        raise DataError(errors["not_zipfile"])


def get_metadata_item(plugin_id):
    """
    Get the metadata_model representation of the plugin
    :param plugin_id: plugin_id
    :type plugin_id: str (str representaion of uuidd)
    :returns: MetadataModel  object
    :rtype: metadata_model.MetadataModel
    """

    item = MetadataModel.get(plugin_id)
    return item


@app.route("/plugin", methods=["POST"])
def upload():
    """
    End point for processing QGIS plugin data POSTed by the user
    :param data: plugin
    :type data: binary data
    :returns: tuple (http response, http code)
    :rtype: tuple (flask.wrappers.Response, int)
    """

    try:
        post_data = request.get_data()
        validate_user_data(post_data)

        # Extract plugin metadata
        plugin_zipfile = zipfile.ZipFile(BytesIO(post_data), "r", zipfile.ZIP_DEFLATED, False)
        metadata_path = plugin_parser.metadata_path(plugin_zipfile)
        metadata = plugin_parser.metadata_contents(plugin_zipfile, metadata_path)

        # Get the plugins root dir. This is what QGIS references when handling plugins
        content_disposition = plugin_parser.zipfile_root_dir(plugin_zipfile)
        logging.info("Content Disposition: %s", content_disposition)

        # Allocate a unique ID. Pluign here on out will be referred to as this
        plugin_id = str(uuid.uuid4())
        logging.info("Plugin Id: %s", plugin_id)

        # Upload the plugin to s3
        aws.s3_put(post_data, repo_bucket_name, plugin_id, content_disposition)
        logging.info("Plugin Upload to s3: %s", plugin_id)

        # Update metadata database
        MetadataModel.update_metadata_db(metadata, plugin_id, content_disposition)
        logging.info("Metadata updated for plugin: %s", plugin_id)
        plugin = get_metadata_item(plugin_id)
        return format_response(MetadataModel.json_dump_item(plugin), 201)

    except DataError as error:
        return format_error(error.msg, 500)

    except Exception as error:
        logging.error("Error: %s", error)
        return format_error("Upload failed :See logs", 500)


@app.route("/plugin", methods=["GET"])
def get_all():
    """
    List all plugin's metadata
    :returns: tuple (http response, http code)
    :rtype: tuple (flask.wrappers.Response, int)
    """

    try:
        return format_response(MetadataModel.json_dump_model(), 200)

    except Exception as error:
        logging.error("Error: %s", error)
        return format_error("Request failed :See logs", 500)


@app.route("/plugin/<plugin_id>", methods=["GET"])
def get_item(plugin_id):
    """
    Takes a plugin_id as input and returns the metadata of the
    one associated plugin to this Id
    :param plugin_id: plugin_id
    :type data: string
    :returns: tuple (http response, http code)
    :rtype: tuple (flask.wrappers.Response, int)
    """

    try:
        plugin = get_metadata_item(plugin_id)
        if not plugin:
            raise DataError("Plugin not found")
        return format_response(MetadataModel.json_dump_item(plugin), 200)

    except DataError as error:
        return format_error(error.msg, 500)
    except Exception as error:
        logging.error("Error: %s", error)
        return format_error("Request failed :See logs", 500)


@app.route("/plugin/<plugin_id>", methods=["DELETE"])
def delete(plugin_id):
    """
    Takes a plugin_id as input and adds an end-date to the
    metadata record associated to the Id
    :param plugin_id: plugin_id
    :type data: string
    :returns: tuple (http response, http code)
    :rtype: tuple (flask.wrappers.Response, int)
    """

    try:
        logging.info("Attempting to delete record: %s", plugin_id)
        plugin = get_metadata_item(plugin_id)

        plugin.update(actions=[MetadataModel.ended_at.set(datetime.now()), MetadataModel.updated_at.set(datetime.now())])
        plugin = get_metadata_item(plugin_id)
        return format_response(MetadataModel.json_dump_item(plugin), 200)

    except Exception as error:
        logging.error("Error: %s", error)
        return format_error("Request failed :See logs", 500)


@app.route("/plugins.xml", methods=["GET"])
def qgis_plugin_xml():
    """"
    Get xml describing current plugins
    """

    try:
        # Upload plugin xml
        xml = plugin_xml.generate_xml_body(repo_bucket_name, aws_region)
        logging.info("Returnig plugin xml to user")
        return app.response_class(response=xml, status=200, mimetype="text/xml")
    except DataError as error:
        return format_error("Request failed :See logs", 500)
    except Exception as error:
        logging.error("Error: %s", error)
        return format_error("Request failed :See logs", 500)


if __name__ == "__main__":
    app.run(debug=True)
