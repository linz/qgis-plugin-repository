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

    Script for reading plugins in a dir to the plugin repository
    Requires the following environmental variables to be set:
        * AWS_ACCESS_KEY_ID
        * AWS_SECRET_ACCESS_KEY
        * AWS_SESSION_TOKEN
        * AWS_REGION

"""

import os
import re
import zipfile
import argparse
from subprocess import check_output
import requests


def create_new_metadata_record(table_name, plugin_id, stage=None):
    """
    Create initial metadata record via utils/new_plugin_record.sh
    :param table_name: The Dynamodb table where metadata records are stored
    :type table_name: str
    :param plugin_id: The plugin id - This must match the plugin root dir
    :type plugin_id: str
    :param stage: The plugin stage. None for prd else "dev"
    :type stage: str
    :returns: The database secret
    :rtype: str
    """

    source = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(source, "new_plugin_record.sh")

    cmd = f"{script} -t {table_name} -p {plugin_id}"
    if stage:
        cmd = cmd + f" -s {stage}"

    new_record = check_output(
        [cmd],
        shell=True,
        env={
            "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY"),
            "AWS_SESSION_TOKEN": os.environ.get("AWS_SESSION_TOKEN"),
            "AWS_DEFAULT_REGION": os.environ.get("AWS_REGION"),
        },
    )

    match = re.search(r"(secret=)(?P<secret>.*)(\s)(?P<hash>hash.*)", new_record.decode("utf-8"))
    return match.group("secret")


def zipfile_root_dir(plugin_zipfile):
    """
    The plugin file must equal that of the plugin root dir name
    :param plugin_zipfile: Zipfile obj representing the plugin
    :type plugin_zipfile: zipfile.ZipFile
    :returns:  Root dir name
    :rtype: str
    """

    # Get root dir
    filelist = plugin_zipfile.filelist
    plugin_root = set(path.filename.split(os.sep)[0] for path in filelist)
    if len(plugin_root) > 1:
        print("Multiple directories exists at the root level. There should only be one")
    if not plugin_root:
        print("The plugin has no root directory. One must exist")
    plugin_root = next(iter(plugin_root))
    return plugin_root


def post_plugin(base_url, plugin, plugin_id, secret, stage=None):
    """
    Post the plugin to the plugin repository via the API
    :param base_url: API url
    :type base_url: str
    :param plugin: Plugin binary
    :type plugin: 'b
    :param plugin_id: The plugin id - This must match the plugin root dir
    :type plugin_id: str
    :param secret: Plugin secret required to modify the plugin
    :type secret: str
    :param stage: The plugin stage. None for prd else dev
    :type stage: str
    :returns:  Request response
    :rtype: requests.response
    """

    header = {"Authorization": f"Bearer {secret}", "content-type": "application/octet-stream"}
    url = f"{base_url}plugin/{plugin_id}"
    if stage:
        url = url + f"?stage={stage}"
    return requests.post(url, data=plugin, headers=header)


def upload_plugins(plugin_directory, table_name, base_url, stage=None):
    """
    Post the plugin to the plugin repository via the API
    :param plugin_directory: path to direcory of plugins to post to repo
    :type plugin_directory: str
    :param table_name: The Dynamodb table where the repo metadata is kept
    :type table_name: str
    :param base_url: API url
    :type base_url: str
    :param stage: The plugin stage. None for prd else "dev"
    :type stage: str
    :returns: Dict of failed uploads
    :rtype: dict
    """

    failed = {}

    # Iterate over directory of plugins to migrate
    for plugin_filename in os.listdir(plugin_directory):
        plugin_path = os.path.join(plugin_directory, plugin_filename)
        if zipfile.is_zipfile(plugin_path):
            with zipfile.ZipFile(plugin_path, "r") as plugin_zipfile:
                plugin_id = zipfile_root_dir(plugin_zipfile)
                secret = create_new_metadata_record(table_name, plugin_id, stage)
            with open(plugin_path, "rb") as f:
                # Post the plugin
                response = post_plugin(base_url, f, plugin_id, secret, stage)
                if response.status_code != 201:
                    failed[plugin_id] = response.content
                else:
                    print(f"{plugin_id}: {secret}")
        else:
            continue

    return failed


if __name__ == "__main__":
    users_args = argparse.ArgumentParser()
    users_args.add_argument("-d", "--plugin-dir", action="store", dest="plugin_directory", required=True)
    users_args.add_argument("-t", "--table-name", action="store", dest="table_name", required=True)
    users_args.add_argument("-u", "--url", action="store", dest="base_url", required=True)
    users_args.add_argument("-s", "--stage", action="store", dest="stage", default=None)
    args = users_args.parse_args()

    failures = upload_plugins(args.plugin_directory, args.table_name, args.base_url, args.stage)

    if failures:
        print("!!! UPLOAD FAILED !!!")
        for k, v in failures.items():
            print(f"{k} failed with {v}")
