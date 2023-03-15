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

    Custom Error class

"""
from typing import Optional

from flask import Response, jsonify
from werkzeug.exceptions import HTTPException

from src.plugin.log import get_log


class DataError(Exception):
    """
    Custom error for catch APP data errors
    """

    http_code: int
    msg: str

    def __init__(self, http_code: int, msg: str):
        super().__init__(msg)
        self.msg = msg
        self.http_code = http_code

    def __str__(self):
        return repr(self.msg)


def handle_error(e: Exception) -> tuple[Response, int]:
    """
    Catch python standard exception
    """

    response_body = {"message": "Internal Server Error"}
    get_log().error("Exception", exception=e)

    return jsonify(response_body), 500


def handle_http_error(e: HTTPException) -> tuple[Response, Optional[int]]:
    """
    Catch HTTP exceptions
    """

    response_body = {"message": e.description}
    get_log().error("Exception", exception=e)

    return jsonify(response_body), e.code


def handle_data_error(e: DataError) -> tuple[Response, int]:
    """
    Custom error
    """

    response_body = {"message": e.msg}
    get_log().info("ResponseMessage", message=e.msg, httpCode=e.http_code)

    return jsonify(response_body), e.http_code


def add_data_error_handler(app):
    """
    Register error handlers
    """

    app.register_error_handler(DataError, handle_data_error)
    app.register_error_handler(HTTPException, handle_http_error)
    app.register_error_handler(Exception, handle_error)
