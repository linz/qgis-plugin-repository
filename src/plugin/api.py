import configparser
import io
import json
import logging
import os
import re
import zipfile

import boto3
from botocore.exceptions import ClientError
from flask import Flask, request
from werkzeug.utils import secure_filename

# UPLOAD_ FOLDER = '/tmp/'
UPLOAD_FOLDER = "/home/splanzer/temp/test"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Repository
if os.environ.get("REPO_BUCKET_NAME") is not None:
    REPO_BUCKET_NAME = os.environ["REPO_BUCKET_NAME"]
else:
    REPO_BUCKET_NAME = "qgis-plugin-repository"


# local testing only
def format_response(success, http_code, reason="", data=None):
    res_body = {"success": success, "reason": reason, "data": data}
    response = app.response_class(response=json.dumps(res_body), status=http_code, mimetype="application/json")
    return response


def metadata_contents(plugin_zip, metadata_path):
    """
    Return metadata.txt contents that is stored in
    the plugin .zip file
    """

    metadata = plugin_zip.open(metadata_path)
    metadata = str(metadata.read(), "utf-8")
    config_parser = configparser.ConfigParser()
    config_parser.read_file(io.StringIO(metadata))
    return config_parser


def get_metadata_path(plugin_zip):
    """
    Returns a list of possible metadata.txt matches
    The regex applied to the zipfles namelist only matches
    one dir deep - therefore it will either return an list with
    one item (path to metadata.txt) else an empty list. If its
    is an empty list that is returned, the metadata.txt was not found
    """

    plugin_files = plugin_zip.namelist()
    metadata_path = [i for i in plugin_files if re.search(r"^\w*\/{1}metadata.txt", i)]
    return metadata_path


def upload_file_to_s3(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then same as file_name
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client("s3")
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False, e
    return True, response


@app.route("/list", methods=["GET"])
def list_all():
    return "TODO"


@app.route("/upload", methods=["POST"])
def upload():
    print(request)
    if "file" not in request.files:
        return "No user_file key in request.files"

    file = request.files["file"]
    if not file:
        return "Invalid file uploaded"

    # should use content-type as-well to validate this
    if not file.filename.endswith(".zip"):
        return "File is not a zip"

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    file.close()

    # Extract plugin metadata
    zfile = zipfile.ZipFile(filepath, "r")
    metadata_path = get_metadata_path(zfile)
    metadata_path = metadata_path[0]
    plugn_metadata = metadata_contents(zfile, metadata_path)
    pl_name = plugn_metadata["general"]["name"]
    pl_version = plugn_metadata["general"]["version"]
    return "{0}-{1}".format(pl_name, pl_version)
    # upload the file
    # success, response = upload_file_to_s3(filepath, REPO_BUCKET_NAME, filename)


@app.route("/remove", methods=["DELETE"])
def remove():
    return "TODO"


if __name__ == "__main__":
    app.run(debug=True)
