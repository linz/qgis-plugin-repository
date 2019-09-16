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

    Model for dynamoDB

"""


# pylint: disable=too-few-public-methods

import os
from datetime import datetime

from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute
from pynamodb.models import Model


class MetadataModel(Model):
    """
    metadata db model
    """

    class Meta:
        """
        db metadata
        """

        table_name = os.environ.get("PLUGINS_TABLE_NAME", "qgis-plugin-repo-metadata")
        region = os.environ.get("REGION", "ap-southeast-2")

    id = UnicodeAttribute(hash_key=True, null=False)
    created_at = UTCDateTimeAttribute(null=False, default=datetime.now())
    updated_at = UTCDateTimeAttribute(null=False, default=datetime.now())
    name = UnicodeAttribute(null=False)
    qgis_minimum_version = UnicodeAttribute(null=False)
    qgis_maximum_version = UnicodeAttribute(null=True)
    description = UnicodeAttribute(null=False)
    about = UnicodeAttribute(null=False)
    version = UnicodeAttribute(null=False)
    author_name = UnicodeAttribute(null=False)
    email = UnicodeAttribute(null=False)
    changelog = UnicodeAttribute(null=True)
    experimental = UnicodeAttribute(null=True, default="False")
    deprecated = UnicodeAttribute(null=True, default="False")
    tags = UnicodeAttribute(null=True)
    homepage = UnicodeAttribute(null=True)
    repository = UnicodeAttribute(null=False)
    tracker = UnicodeAttribute(null=True)
    icon = UnicodeAttribute(null=True)
    category = UnicodeAttribute(null=True)
    file_name = UnicodeAttribute(null=False)

    def __iter__(self):
        for name, attr in self._get_attributes().items():
            yield name, attr.serialize(getattr(self, name))
