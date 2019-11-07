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
    Custom Error class
"""

from flask import jsonify
from src.plugin.log import get_log


class DataError(Exception):
    """
    Custom error for catch APP data errors
    """

    http_code: int
    msg: str

    def __init__(self, http_code: int, msg: str):
        super(DataError, self).__init__(msg)
        self.msg = msg
        self.http_code = http_code

    def __str__(self):
        return repr(self.msg)


def handle_error(e: Exception):
    """
    Catch python standard exception
    """

    response_body = {"message": "Internal Server Error"}
    get_log().error("Exception", exception=e)

    return jsonify(response_body), 500


def handle_data_error(e: DataError):
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
    app.register_error_handler(Exception, handle_error)
