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


import os
from datetime import datetime

from pynamodb.attributes import UnicodeAttribute, BooleanAttribute, UTCDateTimeAttribute
from pynamodb.models import Model


class MetadataModel(Model):
    """
    metadata db model
    """

    class Meta:
        """
        db metadata
        """

        table_name = os.environ["PLUGINS_TABLE_NAME"]
        region = os.environ["REGION"]

    id = UnicodeAttribute(hash_key=True, null=False)
    plugin_id = UnicodeAttribute(null=False)
    name = UnicodeAttribute(null=False)
    version = UnicodeAttribute(null=False)
    author_name = BooleanAttribute(null=False)
    email = UnicodeAttribute(null=False)
    description = UnicodeAttribute(null=True)
    about = UnicodeAttribute(null=True)
    qgis_minimum_version = UnicodeAttribute(null=False)
    homepage = UnicodeAttribute(null=True)
    repository = UnicodeAttribute(null=True)
    experimental = BooleanAttribute(null=False)
    updated_at = UTCDateTimeAttribute(null=False, default=datetime.now())

    def __iter__(self):
        for name, attr in self._get_attributes().items():
            yield name, attr.serialize(getattr(self, name))
