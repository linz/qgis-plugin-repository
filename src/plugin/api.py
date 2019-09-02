import os
import re
import json
import logging
import zipfile
import configparser

from io import BytesIO, StringIO
from flask import Flask, request
from botocore.exceptions import ClientError
import boto3

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

    response_body = {'message': message}
    response = app.response_class(
        response=json.dumps(response_body),
        status=http_code,
        mimetype="application/json")
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


def upload_plugin_to_s3(data, bucket, object_name):
    """
    Upload plugin file to S3 plugin repository bucket
    """

    try:
        response = s3_client.put_object(Body=data, Bucket=bucket, Key=object_name)

    except ClientError as error:
        logging.error("s3 PUT error: %s", error)
        return False, str(error)

    logging.info("s3 PUT response: %s", response)
    return True, response


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
    plugin_name = metadata["general"]["name"] + metadata["general"]["version"]
    success, response = upload_plugin_to_s3(data, repo_bucket_name, plugin_name)

    # Respond to the user
    if success:
        logging.info("Plugin Upload: %s", plugin_name)
        return format_response({"pluginName": plugin_name}, 201)

    else:
        logging.error("Plugin Upload Failed: %s", plugin_name)
        return format_error("Upload failed :See logs", 400)


if __name__ == "__main__":
    app.run(debug=True)
