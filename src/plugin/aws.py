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

    Database metadata manager

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
    if content_disposition:
        s3_client.put_object(Body=data, Bucket=bucket, Key=object_name, ContentDisposition=content_disposition)
    else:
        s3_client.put_object(Body=data, Bucket=bucket, Key=object_name)


def s3_head_bucket(bucket):
    """
    For healthcheck
    :param bucket: bucket name
    :type bucket: str
    """

    s3_client = boto3.resource("s3")
    s3_client.meta.client.head_bucket(Bucket=bucket)
