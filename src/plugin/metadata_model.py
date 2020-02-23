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

# Database to metadata.txt mapping
DBMD_MAP = {
    "name": "name",
    "version": "version",
    "qgis_minimum_version": "qgisMinimumVersion",
    "qgis_maximum_version": "qgisMaximumVersion",
    "description": "description",
    "about": "about",
    "author_name": "author",
    "email": "email",
    "changelog": "changelog",
    "experimental": "experimental",
    "deprecated": "deprecated",
    "tags": "tags",
    "homepage": "homepage",
    "repository": "repository",
    "tracker": "tracker",
    "icon": "icon",
    "category": "category",
}


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
        Yields all version zero plugin metadata
        :returns: json describing plugin metadata
        :rtype: json
        """

        for item in cls.scan(cls.item_version == "0".zfill(RECORD_FILL)):
            yield json.loads(json.dumps(item.attribute_values, cls=ModelEncoder))

    @classmethod
    def current_version_zeros(cls):
        """
        Returns a json representation of all plugins
        :param current_only: If True, filter on only records not enddated (archived)
        :type current_only: Boolean
        :returns: json describing plugin metadata
        :rtype: json
        """

        v_zeros = []
        for item in cls.all_version_zeros():
            if not item.get("ended_at"):
                v_zeros.append(item)
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
            if version.item_version != "metadata":
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
        action_list = []

        for db_model_key, metadata_key in DBMD_MAP.items():
            if metadata_key in general_metadata and general_metadata[metadata_key] != "":
                model_item = getattr(cls, db_model_key)
                action_list.append(model_item.set(general_metadata.get(metadata_key)))

        # set all standard actions for the update
        action_list.extend(
            [
                cls.qgis_maximum_version.set(
                    general_metadata.get(
                        "qgisMaximumVersion", f"{general_metadata.get('qgisMinimumVersion').split('.')[0]}.999"
                    )
                ),
                cls.revisions.set(version_zero.revisions + 1),
                cls.ended_at.remove(),
                cls.created_at.set(
                    datetime.now()
                    if "created_at" not in version_zero.attribute_values
                    else version_zero.attribute_values["created_at"]
                ),
                cls.updated_at.set(datetime.now()),
                cls.file_name.set(filename),
            ]
        )
        version_zero.update(actions=action_list, condition=(cls.revisions == version_zero.revisions))

    @classmethod
    def insert_revision(cls, attributes):
        """
        Insert a version of the previous version zero record
        for audit purposes
        :param attributes: dict of properties representing the former version zero metadata
        :type attributes: dict
        """

        attributes["item_version"] = str(attributes["revisions"]).zfill(RECORD_FILL)
        revision = cls(**attributes)
        revision.save(condition=(cls.revisions.does_not_exist() | cls.id.does_not_exist()))

    @classmethod
    def new_plugin_version(cls, metadata, plugin_id, filename):
        """
        If a new version of an existing plugin is submitted via the API
        update the version zero record with its details and
        store a revision of the former version zero entry for
        database audit purposes.
        :param metadata: ConfigParser representation of metadata.txt
        :type metadata: configparser.ConfigParser
        :param plugin_id: plugin root folder. Makes up the PK
        :type plugin_id: str
        :param filename: filename of plugin.zip in datastore (currently s3)
        :type filename: str
        :returns: json describing plugin metadata
        :rtype: json
        """

        result = cls.query(plugin_id, cls.item_version == "0".zfill(RECORD_FILL))
        try:
            version_zero = next(result)
        except StopIteration:
            get_log().error("PluginNotFound")
            raise DataError(400, "Plugin Not Found")
        # Update version zero
        cls.update_version_zero(metadata, version_zero, filename)
        get_log().info("VersionZeroUpdated")

        # Insert v0 into revision
        cls.insert_revision(version_zero.attribute_values)
        get_log().info("RevisionInserted", pluginId=plugin_id, revision=version_zero.revisions)

        updated_metadata = json.loads(json.dumps(version_zero.attribute_values, cls=ModelEncoder))
        get_log().info("MetadataStored", metadata=updated_metadata)

        return updated_metadata

    @classmethod
    def validate_token(cls, token, plugin_id):
        """
        Check the bearer-token against the plugins secret to ensure
        the user can modify the plugin.
        :param token: bearer-token as submitted by user. Ensures user can modify plugin record
        :type token: str
        :param plugin_id: plugin root folder. Makes up the PK
        :type plugin_id: str
        """

        result = cls.query(plugin_id, cls.item_version == "metadata")
        try:
            metadata = next(result)
        except StopIteration:
            get_log().error("PluginNotFound")
            raise DataError(400, "Plugin Not Found")
        if token != metadata.secret:
            get_log().error("InvalidToken")
            raise DataError(403, "Invalid token")

    @classmethod
    def archive_plugin(cls, plugin_id):
        """
        Retire plugin by adding a enddate to the metadata record
        :param plugin_id: plugin Id. Makes up the PK
        :type plugin_id: str
        :returns: json describing archived plugin metadata
        :rtype: json
        """
        result = cls.query(plugin_id, cls.item_version == "0".zfill(RECORD_FILL))
        try:
            version_zero = next(result)
        except StopIteration:
            get_log().error("PluginNotFound")
            raise DataError(400, "Plugin Not Found")
        version_zero.update(
            actions=[
                cls.ended_at.set(datetime.now()),
                cls.updated_at.set(datetime.now()),
                cls.revisions.set(version_zero.revisions + 1),
            ]
        )
        # Insert former v0 into revision
        cls.insert_revision(version_zero.attribute_values)
        get_log().info("RevisionInserted", pluginId=plugin_id, revision=version_zero.revisions)
        updated_metadata = json.loads(json.dumps(version_zero.attribute_values, cls=ModelEncoder))
        get_log().info("MetadataStored", metadata=updated_metadata)

        return updated_metadata
