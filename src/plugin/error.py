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


class DataError(Exception):
    """
    Custom error for catch APP data errors
    """

    def __init__(self, msg):
        super(DataError, self).__init__(msg)
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
