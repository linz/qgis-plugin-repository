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

    Interactions with repo's s3 data store

"""


import boto3


def s3_put(data, bucket, object_name, content_disposition=None):
    """
    Upload plugin file to S3 plugin repository bucket

    :param data: Object data
    :type data: binary
    :param bucket: bucket name
    :type bucket: str
    """

    s3_client = boto3.client("s3")
    s3_client.put_object(Body=data, Bucket=bucket, Key=object_name, ContentDisposition=content_disposition)


def s3_head_bucket(bucket):
    """
    For healthcheck
    :param bucket: bucket name
    :type bucket: str
    """

    s3_client = boto3.resource("s3")
    s3_client.meta.client.head_bucket(Bucket=bucket)
