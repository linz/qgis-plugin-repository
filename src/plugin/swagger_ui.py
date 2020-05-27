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
"""

import json
import os
from flask import Blueprint, send_from_directory, render_template, request


def get_swagger_ui_blueprint(base_url, stage, api_version, dns):
    """
    Factory function for setting of swagger_ui blueprint
    :param base_url: docs endpoint
    :type base_url: str
    :param stage: serverless stage (eg. dev / prd)
    :type stage: str
    :param api_version: Verison of the api. e.g 'v1'
    :type api_version: str
    :param dns: 'true' if DNS is in use or 'false' if using unmapped api gateway url
    :type dns: str
    :returns: flask blueprint
    :rtype: flask.blueprints.Blueprint

    """

    blueprint_name = "swagger_ui"
    static_path = "./swagger_ui"

    swagger_ui = Blueprint(
        blueprint_name, __name__, static_folder=f"{static_path}/static", template_folder=f"{static_path}/templates"
    )

    if dns in [True, "true", "True"]:
        docs_base_url = base_url
        api_url = f"/{api_version}/docs/swagger.json"
    else:
        docs_base_url = f"/{stage}/{base_url}"
        api_url = f"/{stage}/{api_version}/docs/swagger.json"

    default_config = {"app_name": "Swagger UI", "dom_id": "#swagger-ui", "url": api_url, "layout": "StandaloneLayout"}

    fields = {"base_url": docs_base_url, "app_name": default_config.pop("app_name"), "config_json": json.dumps(default_config)}

    @swagger_ui.route("/")
    @swagger_ui.route("/<path:path>")
    # pylint: disable=unused-variable
    def show(path=None):
        """
        Show swagger_ui
        """
        if not path or path == "index.html":
            if not default_config.get("oauth2RedirectUrl", None):
                default_config.update({"oauth2RedirectUrl": os.path.join(request.base_url, "oauth2-redirect.html")})
                fields["config_json"] = json.dumps(default_config)
            return render_template("index.template.html", **fields)
        return send_from_directory(os.path.join(swagger_ui.root_path, swagger_ui.static_folder), path)

    return swagger_ui
