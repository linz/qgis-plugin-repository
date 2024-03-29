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

    Flask API for managing the storage and retrieval QGIS Plugins in S3

"""
# pylint: disable=W0703,E0237


import os
import time
import uuid
import zipfile
from io import BytesIO
from re import match

import ulid
from flask import Flask, g, jsonify, request

from src.plugin import aws, plugin_parser, plugin_xml, swagger_ui
from src.plugin.error import DataError, add_data_error_handler
from src.plugin.log import get_log
from src.plugin.metadata_model import MetadataModel

app = Flask(__name__)


app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
add_data_error_handler(app)

AUTH_PREFIX = "bearer "
DEFUALT_STAGE = ""
API_VERSION = "v1"
# Repository bucket name
repo_bucket_name = os.environ.get("REPO_BUCKET_NAME")

# Deployment stage
aws_stage = os.environ.get("STAGE")

# AWS region
aws_region = os.environ.get("AWS_REGION", None)

# Git commit SHA
git_sha = os.environ.get("GIT_SHA", None)
git_tag = os.environ.get("GIT_TAG", None)

# Swagger documentation
swagger_url = "/docs"
api_url = f"/{aws_stage}/docs/swagger.json"
blueprint_name = "swagger_ui"
static_path = "./swagger_ui"
swaggerui_blueprint = swagger_ui.get_swagger_ui_blueprint(swagger_url, api_url, aws_stage, blueprint_name, static_path)

app.register_blueprint(swaggerui_blueprint, url_prefix=swagger_url)


@app.before_request
def before_request():
    """
    Before request gather log details
    """

    g.start_time = time.time()
    g.request_id = str(ulid.new())
    get_log().info("CorrelationId", correlationId=request.headers.get("x-linz-correlation-id", str(ulid.new())))


@app.after_request
def after_request(response):
    """
    After request logout API/Lambda metrics
    """

    get_log().info(
        "RequestMetadata",
        uri=request.path,
        method=request.method,
        status=response.status,
        args=dict(request.args),
        duration=(time.time() - g.start_time) * 1000,
        lambdaName=os.environ["AWS_LAMBDA_FUNCTION_NAME"],
        lambdaMemory=os.environ["AWS_LAMBDA_FUNCTION_MEMORY_SIZE"],
        lambdaVersion=os.environ["AWS_LAMBDA_FUNCTION_VERSION"],
        lambdaLogStreamName=os.environ["AWS_LAMBDA_LOG_STREAM_NAME"],
        lambdaRegion=os.environ["AWS_REGION"],
    )

    response.headers["X-Request-ID"] = g.request_id
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
    return response


def get_access_token(headers):
    """
    Parse the bearer token
    """

    auth_header = headers.get("authorization", None)
    if not auth_header:
        get_log().error("InvalidToken")
        raise DataError(403, "Invalid token")
    if not auth_header.lower().startswith(AUTH_PREFIX):
        get_log().error("InvalidToken", authHeader=auth_header)
        raise DataError(403, "Invalid token")
    return auth_header[len(AUTH_PREFIX) :]


def validate_stage(plugin_stage):
    """
    # As query params that are not "?qgis=x"can not be sent via QGIS,
    # at this stage only dev and prd stages are able to be stored
    # dev is opt in via `?stage=dev. If the `stage` query param is not supplied
    # the API interactions are considered to be for prd plugins
    """

    if plugin_stage not in ["dev", ""]:
        get_log().error("stage is not recognised")
        raise DataError(400, "stage is not recognised")
    return plugin_stage


@app.route(f"/{API_VERSION}/plugin/<plugin_id>", methods=["POST"])
def upload(plugin_id):
    """
    End point for processing QGIS plugin data POSTed by the user
    If the query param "?stage" is not supplied, plugins POSTed are
    considered production. if `?stage=dev` is used the plugin
    is stored as a dev version
    :param data: plugin
    :type data: binary data
    :returns: tuple (http response, http code)
    :rtype: tuple (flask.wrappers.Response, int)
    """

    plugin_stage = request.args.get("stage", DEFUALT_STAGE)
    validate_stage(plugin_stage)

    post_data = request.get_data()
    if not post_data:
        get_log().error("NoDataSupplied")
        raise DataError(400, "No plugin file supplied")

    # Get users access token from header
    token = get_access_token(request.headers)
    MetadataModel.validate_token(token, plugin_id, plugin_stage)

    # Test the file is a zipfile
    if not zipfile.is_zipfile(BytesIO(post_data)):
        get_log().error("NotZipfile")
        raise DataError(400, "Plugin file supplied not a Zipfile")

    # Extract plugin metadata
    with zipfile.ZipFile(BytesIO(post_data), "r", zipfile.ZIP_DEFLATED, False) as plugin_zipfile:
        metadata_path = plugin_parser.metadata_path(plugin_zipfile)
        metadata = plugin_parser.metadata_contents(plugin_zipfile, metadata_path)

        # Get the plugins root dir. This is what QGIS references when handling plugins
        g.plugin_id = plugin_parser.zipfile_root_dir(plugin_zipfile)
    if g.plugin_id != plugin_id:
        raise DataError(400, f"Invalid plugin name {g.plugin_id}")

    # Allocate a filename
    filename = str(uuid.uuid4())
    get_log().info("FileName", filename=filename)

    # Upload the plugin to s3
    aws.s3_put(post_data, repo_bucket_name, filename, g.plugin_id)
    get_log().info("UploadedTos3", filename=filename, bucketName=repo_bucket_name)

    # Update metadata database
    try:
        plugin_metadata = MetadataModel.new_plugin_version(metadata, g.plugin_id, filename, plugin_stage)
    except ValueError as error:
        raise DataError(400, str(error)) from error
    return format_response(plugin_metadata, 201)


@app.route(f"/{API_VERSION}/plugin", methods=["GET"])
def get_all_plugins():
    """
    List all plugin's metadata
    :returns: tuple (http response, http code)
    :rtype: tuple (flask.wrappers.Response, int)
    """

    plugin_stage = request.args.get("stage", DEFUALT_STAGE)
    response = list(MetadataModel.all_version_zeros(plugin_stage))
    return format_response(response, 200)


@app.route(f"/{API_VERSION}/plugin/<plugin_id>", methods=["GET"])
def get_plugin(plugin_id):
    """
    Takes a plugin_id as input and returns the metadata of the
    one associated plugin to this Id
    :param plugin_id: plugin_id
    :type data: string
    :returns: tuple (http response, http code)
    :rtype: tuple (flask.wrappers.Response, int)
    """

    plugin_stage = request.args.get("stage", DEFUALT_STAGE)
    g.plugin_id = plugin_id
    return format_response(MetadataModel.plugin_version_zero(plugin_id, plugin_stage), 200)


@app.route(f"/{API_VERSION}/plugin/<plugin_id>/revision", methods=["GET"])
def get_all_revisions(plugin_id):
    """
    Takes a plugin_id and returns all associated plugin revisions
    :param plugin_id: plugin_id
    :type data: string
    :returns: tuple (http response, http code)
    :rtype: tuple (flask.wrappers.Response, int)
    """

    plugin_stage = request.args.get("stage", DEFUALT_STAGE)
    g.plugin_id = plugin_id
    return format_response(MetadataModel.plugin_all_versions(plugin_id, plugin_stage), 200)


@app.route(f"/{API_VERSION}/plugin/<plugin_id>", methods=["DELETE"])
def archive(plugin_id):
    """
    Takes a plugin_id as input and adds an end-date to the
    metadata record associated to the Id
    :param plugin_id: plugin_id
    :type data: string
    :returns: tuple (http response, http code)
    :rtype: tuple (flask.wrappers.Response, int)
    """

    plugin_stage = request.args.get("stage", DEFUALT_STAGE)
    g.plugin_id = plugin_id

    # Get users access token from header
    token = get_access_token(request.headers)
    # validate access token
    MetadataModel.validate_token(token, g.plugin_id, plugin_stage)
    # Archive plugins
    response = MetadataModel.archive_plugin(plugin_id, plugin_stage)
    return format_response(response, 200)


def validate_qgis_version(qgis_version):
    """
    Ensure the query parameter is a valid version string
    :param qgis_version: qgis version to filter by
    :type qgis_version: string
    """

    if not match(r"^\d+\.\d+(\.\d+)?$", qgis_version):
        get_log().error("Invalid QGIS version")
        raise DataError(400, "Invalid QGIS version")


@app.route(f"/{API_VERSION}/<stage>/plugins.xml", methods=["GET"])
@app.route(f"/{API_VERSION}/plugins.xml", defaults={"stage": ""}, methods=["GET"])
def qgis_plugin_xml(stage):
    """
    Get xml describing current plugins
    :returns: xml doc describing current (version==0) plugins
    :rtype: tuple (flask.wrappers.Response, int)
    """

    qgis_version = request.args.get("qgis", "0.0.0")
    plugin_stage = stage

    validate_qgis_version(qgis_version)

    xml = plugin_xml.generate_xml_body(repo_bucket_name, aws_region, qgis_version, plugin_stage)
    return app.response_class(response=xml, status=200, mimetype="text/xml")


@app.route(f"/{API_VERSION}/version", methods=["GET"])
def version():
    """
    Return git commit SHA the API was deploy from
    :returns: Returns json object {hash: <git_sha>, 'version': <tag, if no tag git_sha>}
    :rtype: json"""

    return format_response({"version": git_tag, "hash": git_sha}, 200)


@app.route(f"/{API_VERSION}/ping", methods=["GET"])
def ping():
    """
    Ping to confirm the service is up
    """

    return app.response_class(status=200)


@app.route(f"/{API_VERSION}/health", methods=["GET"])
def health():
    """
    Ping to confirm the service is up
    """

    checks = {}

    # check database connection
    MetadataModel.all_version_zeros(DEFUALT_STAGE)
    checks["db"] = {"status": "ok"}

    # check s3 connection
    aws.s3_head_bucket(repo_bucket_name)
    checks["s3"] = {"status": "ok"}

    # Anything not a 200 has been caught as an
    # error and the health-checks have failed
    get_log().info({"status": "ok", "details": checks})
    return format_response({"status": "ok"}, 200)


if __name__ == "__main__":
    app.run(debug=True)
