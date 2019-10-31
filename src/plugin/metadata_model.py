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
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, NumberAttribute
from pynamodb.models import Model
from src.plugin.error import DataError
from src.plugin.log import get_log

RECORD_FILL = 6


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
    item_version = UnicodeAttribute(range_key=True, null=False)
    revisions = NumberAttribute(null=False)
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
    secret = UnicodeAttribute(null=True)

    def __iter__(self):
        for name, attr in self._get_attributes().items():
            yield name, attr.serialize(getattr(self, name))

    @classmethod
    def all_version_zeros(cls):
        """
        Returns a json representation of all plugins
        metadata for the most current version
        :returns: json describing plugin metadata
        :rtype: json
        """

        v_zeros = []
        for item in cls.scan(cls.item_version == "0".zfill(RECORD_FILL)):
            v_zeros.append(json.loads(json.dumps(item.attribute_values, cls=ModelEncoder)))
        return v_zeros

    @classmethod
    def plugin_version_zero(cls, plugin_id):
        """
        Returns the most current metadata for the
        plugin matching the plugin_id parameter
        :param plugin_id: The plugin_id for the record to retrieve form the database.
        :type plugin_id: str
        :returns: json describing plugin metadata
        :rtype: json
        """

        result = cls.query(plugin_id, cls.item_version == "0".zfill(RECORD_FILL))
        if result:
            version_zero = next(result)
        return json.loads(json.dumps(version_zero.attribute_values, cls=ModelEncoder))

    @classmethod
    def plugin_all_versions(cls, plugin_id):
        """
        Returns the all versions of metadata for the
        plugin matching the plugin_id parameter
        :param plugin_id: The plugin_id for the record to retrieve form the database.
        :type plugin_id: str
        :returns: json describing plugin metadata
        :rtype: json
        """

        versions = []
        result = cls.query(plugin_id)
        for version in result:
            versions.append(json.loads(json.dumps(version.attribute_values, cls=ModelEncoder)))
        return versions

    @classmethod
    def update_version_zero(cls, metadata, version_zero, filename):

        """
        Update dynamodb metadata store for uploaded plugin

        :param metadata: ConfigParser representation of metadata.txt
        :type metadata: configparser.ConfigParser
        :param version_zero: metadata object
        :type version_zero: metadata_model.Metadata
        :param filename: filename of plugin.zip in datastore (currently s3)
        :type filename: str
        """

        general_metadata = metadata["general"]

        version_zero.update(
            actions=[
                cls.name.set(general_metadata.get("name", None)),
                cls.version.set(general_metadata.get("version", None)),
                cls.revisions.set(version_zero.revisions + 1),
                cls.qgis_minimum_version.set(general_metadata.get("qgisMinimumVersion", None)),
                cls.qgis_maximum_version.set(general_metadata.get("qgisMaximumVersion", None)),
                cls.description.set(general_metadata.get("description", None)),
                cls.about.set(general_metadata.get("about", None)),
                cls.author_name.set(general_metadata.get("author", None)),
                cls.email.set(general_metadata.get("email", None)),
                cls.changelog.set(general_metadata.get("changelog", None)),
                cls.experimental.set(general_metadata.get("experimental", None)),
                cls.deprecated.set(general_metadata.get("deprecated", None)),
                cls.tags.set(general_metadata.get("tags", None)),
                cls.homepage.set(general_metadata.get("homepage", None)),
                cls.repository.set(general_metadata.get("repository", None)),
                cls.tracker.set(general_metadata.get("tracker", None)),
                cls.icon.set(general_metadata.get("icon", None)),
                cls.category.set(general_metadata.get("category", None)),
                cls.file_name.set(filename),
            ],
            condition=(cls.revisions == version_zero.revisions),
        )

    @classmethod
    def revision_former_version_zero(cls, attributes):
        """
        Insert a version of the previsous version zero record
        for audit purposes
        :param attributes: dict of properties representing the former version zero metadata
        :type attributes: dict
        """

        attributes["item_version"] = str(attributes["revisions"]).zfill(RECORD_FILL)
        former_record = cls(**attributes)
        former_record.save(condition=(cls.revisions.does_not_exist() | cls.id.does_not_exist()))

    @classmethod
    def new_plugin_version(cls, metadata, content_disposition, filename):
        """
        If a new version of an existing plugin is submitted via the API
        update the version zero record with its details and
        store a revision of the former version zero entry for
        database audit purposes.
        :param metadata: ConfigParser representation of metadata.txt
        :type metadata: configparser.ConfigParser
        :param content_disposition: plugin root folder. Makes up the PK
        :type content_disposition: str
        :param filename: filename of plugin.zip in datastore (currently s3)
        :type filename: str
        """

        result = cls.query(content_disposition, cls.item_version == "0".zfill(RECORD_FILL))
        version_zero = next(result)
        # Update version zero
        cls.update_version_zero(metadata, version_zero, filename)
        get_log().info("VersionZeroUpdated", pluginId=content_disposition)

        # Insert former v0 into revision
        cls.revision_former_version_zero(version_zero.attribute_values)
        version_zero.refresh()
        get_log().info("RevisionInserted", pluginId=content_disposition, revision=version_zero.revisions)

        updated_metadata = json.loads(json.dumps(version_zero.attribute_values, cls=ModelEncoder))
        get_log().info("MetadataStored", metadata=updated_metadata)

        return updated_metadata

    @classmethod
    def validate_token(cls, token, content_disposition):
        """
        Check the bearer-token against the plugins secret to ensure
        the user can modify the plugin.
        :param token: bearer-token as submitted by user. Ensures user can modify plugin record
        :type token: str
        :param content_disposition: plugin root folder. Makes up the PK
        :type content_disposition: str
        """

        result = cls.query(content_disposition, cls.item_version == "metadata")
        metadata = next(result)
        if token != metadata.secret:
            get_log().error("InvalidToken", pluginId=content_disposition)
            raise DataError(403, "Invalid token")
