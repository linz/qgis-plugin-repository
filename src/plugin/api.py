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
from flask import Flask, request
from botocore.exceptions import ClientError
from pynamodb.exceptions import PutError, TableDoesNotExist, TableError, PynamoDBConnectionError
import boto3
from src.plugin.metadata_model import MetadataModel

app = Flask(__name__)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Repository bucket name
if os.environ.get("REPO_BUCKET_NAME") is not None:
    repo_bucket_name = os.environ["REPO_BUCKET_NAME"]
else:
    repo_bucket_name = "qgis-plugin-repository"

# Boto S3 client
s3_client = boto3.client("s3")


def format_error(message, http_code):
    """"
    format error responses
    """

    response_body = {"message": message}
    response = app.response_class(response=json.dumps(response_body), status=http_code, mimetype="application/json")
    return response


def format_response(data, http_code):
    """
    format the http response
    """

    # once metadata handling is delivered, this will always return standard plugin metadata
    response = app.response_class(response=json.dumps(data), status=http_code, mimetype="application/json")
    return response


def get_metadata_path(plugin_zip):
    """
    Returns a list of possible metadata.txt matches.
    The regex applied to the zipfles namelist only matches
    one dir deep - therefore it will either return an list with
    one item (path to metadata.txt) else an empty list. If its
    is an empty list that is returned, the metadata.txt was not found
    """

    plugin_files = plugin_zip.namelist()
    metadata_path = [i for i in plugin_files if re.search(r"^\w*\/{1}metadata.txt", i)]

    logging.info("Plugin metadata path: %s", metadata_path)
    return metadata_path


def metadata_contents(plugin_zipfile, metadata_path):
    """
    Return metadata.txt contents that is stored in
    the plugin .zip file
    """

    metadata = plugin_zipfile.open(metadata_path)
    metadata = str(metadata.read(), "utf-8")
    config_parser = configparser.ConfigParser()
    config_parser.read_file(StringIO(metadata))

    logging.info("Plugin metadata: %s", config_parser)
    return config_parser


def updated_metadata_db(metadata):
    """
    Update dynamodb metadata store for uploaded plugin
    """

    general_metadata = metadata["general"]

    plugin_id = "{0}.{1}".format(general_metadata.get("name"), general_metadata.get("version"))

    plugin = MetadataModel(
        id=str(uuid.uuid4()),
        name=general_metadata.get("name", None),
        version=general_metadata.get("version", None),
        plugin_id=plugin_id,
        qgisMinimumVersion=general_metadata.get("qgisMinimumVersion", None),
        qgisMaximumVersion=general_metadata.get("qgisMaximumVersion", None),
        description=general_metadata.get("description", None),
        about=general_metadata.get("about", None),
        author=general_metadata.get("author", None),
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
    )

    try:
        plugin.save()
        return (None, plugin_id)
    except ValueError as error:
        logging.error("ValueError: %s", error)
        return (("ValueError: {0}").format(error), plugin_id)
    except TableDoesNotExist as error:
        logging.error("TableDoesNotExist: %s", error)
        return ("TableDoesNotExist", plugin_id)
    except TableError as error:
        logging.error("TableError: %s", error)
        return ("TableError", plugin_id)
    except PutError as error:
        logging.error("PutError: %s", error)
        return ("PutError", plugin_id)
    except PynamoDBConnectionError as error:
        logging.error("PynamoDBConnectionError: %s", error)
        return ("PynamoDBConnectionError", plugin_id)


def upload_plugin_to_s3(data, bucket, object_name):
    """
    Upload plugin file to S3 plugin repository bucket
    """

    try:
        response = s3_client.put_object(Body=data, Bucket=bucket, Key=object_name)

    except ClientError as error:
        logging.error("s3 PUT error: %s", error)
        return False

    logging.info("s3 PUT response: %s", response)
    return True


@app.route("/plugin", methods=["POST"])
def upload():
    """
    End point for processing data POSTed by the user
    """

    data = request.get_data()

    # Check data was posted by the user
    if not data:
        logging.error("Data Error: No plugin file supplied")
        return format_error("No plugin file supplied", 400)

    # Store the uploaded data as binary
    zip_buffer = BytesIO(data)

    # Test the file is a zipfile
    if not zipfile.is_zipfile(zip_buffer):
        logging.error("Data Error: Plugin file supplied not a Zipfile")
        return format_error("File must be a zipfile", 400)

    # Extract plugin metadata
    plugin_zipfile = zipfile.ZipFile(zip_buffer, "r", zipfile.ZIP_DEFLATED, False)
    metadata_path = get_metadata_path(plugin_zipfile)
    if not metadata_path:
        logging.error("Data Error: metadata.txt not found")
        return format_error("metadata.txt not found", 400)

    metadata_path = metadata_path[0]
    metadata = metadata_contents(plugin_zipfile, metadata_path)
    # The below will eventually be handle by metadata store method
    error, plugin_name = updated_metadata_db(metadata)
    if error:
        logging.error("Plugin Upload Failed: %s", plugin_name)
        return format_error(error, 400)

    success = upload_plugin_to_s3(data, repo_bucket_name, plugin_name)
    # Respond to the user
    if not success:
        logging.error("Plugin Upload Failed: %s", plugin_name)
        return format_error("Upload failed :See logs", 400)

    logging.info("Plugin Upload: %s", plugin_name)
    return format_response({"pluginName": plugin_name}, 201)


if __name__ == "__main__":
    app.run(debug=True)
