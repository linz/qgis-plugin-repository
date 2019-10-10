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
import json
import logging

from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute
from pynamodb.models import Model


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModelEncoder(json.JSONEncoder):
    """
    Encode json
    """

    # pyint E0202 is a false positive in this case
    # see - https://github.com/PyCQA/pylint/issues/414
    def default(self, o):  # pylint: disable=E0202
        """
        Handle types associated with model for loading to json
        """
        if hasattr(o, "attribute_values"):
            return o.attribute_values
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


class MetadataModel(Model):
    """
    metadata db model

    """

    class Meta:
        """
        db metadata

        Maps metadata.txt value to metadata database.
        Metadata values are described here -
        https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/plugins.html#plugin-metadata-table
        some database keys vary slightly in name than metadata.txt.
        This is as database keys match the qgis plugins.xml and maps
        to the this document (plugins.xml)
        """

        table_name = os.environ.get("PLUGINS_TABLE_NAME", "qgis-plugin-repo-metadata")
        region = os.environ.get("AWS_REGION")

    id = UnicodeAttribute(hash_key=True, null=False)
    created_at = UTCDateTimeAttribute(null=False, default=datetime.now())
    updated_at = UTCDateTimeAttribute(null=False, default=datetime.now())
    ended_at = UTCDateTimeAttribute(null=True)
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

    @classmethod
    def json_dump_model(cls):
        """
        Dump json representation of all items in model
        """

        json_representation = {}
        for plugin in cls.scan():
            json_representation.update(cls.json_dump_item(plugin))
        return json_representation

    @classmethod
    def json_dump_item(cls, plugin):
        """
        Dump json representation of single item in model
        """

        json_representation = {}
        json_representation[plugin.id] = json.loads(json.dumps(plugin.attribute_values, cls=ModelEncoder))
        return json_representation

    @classmethod
    def json_dump_model_current(cls):
        """
        Dump json representation of all items in model.
        Where multiple dates exist for a duplicate
        plugin name + version combination return the
        last updated item.
        """

        most_current = {}
        for plugin_metadata in cls.json_dump_model().values():
            if "ended_at" not in plugin_metadata:
                pluig_ref = plugin_metadata["name"] + "-" + plugin_metadata["version"]
                if pluig_ref in most_current:
                    if plugin_metadata["created_at"] > most_current[pluig_ref]["created_at"]:
                        most_current[pluig_ref] = plugin_metadata
                else:
                    most_current[pluig_ref] = plugin_metadata
        return most_current

    @classmethod
    def update_metadata_db(cls, metadata, plugin_id, plugin_file_name):
        """
        Update dynamodb metadata store for uploaded plugin

        :param metadata: ConfigParser representation of metadata.txt
        :type metadata: configparser.ConfigParser
        :returns: tuple (<error>, <plugin_id>).
                  if successful error == None
                  plugin_id == <plugin_name>+<plugin_version>
        :rtype: tuple
        """

        general_metadata = metadata["general"]
        plugin = cls(
            id=plugin_id,  # partition_key
            name=general_metadata.get("name", None),
            version=general_metadata.get("version", None),
            qgis_minimum_version=general_metadata.get("qgisMinimumVersion", None),
            qgis_maximum_version=general_metadata.get("qgisMaximumVersion", None),
            description=general_metadata.get("description", None),
            about=general_metadata.get("about", None),
            author_name=general_metadata.get("author", None),
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
            file_name=plugin_file_name,
        )

        plugin.save()
