#!/bin/bash

# Usage:
# ./new_plugin_record.sh -t '<dynamodb table>' -p <plugin_id> -s <plugin stage>

TABLE_NAME=""
PLUGIN_ID=""
PLUGIN_STAGE=""
VER_ZERO_JSON="{}"
METADATA_JSON="{}"
SECRET=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 64 | head -n 1)
SECRET_HASH=$(echo -n "$SECRET" | sha512sum | tr -d "[:space:]-")

# Parse args
while [ $# -gt 1 ]
do
key="$1"

case $key in
    -t|--table)
    TABLE_NAME="$2"
    shift
    ;;
    -p|--plugin-id)
    PLUGIN_ID="$2"
    shift
    ;;
    -s|--stage)
    PLUGIN_STAGE="$2"
    shift
    ;;
esac
shift
done

# JSON reprsentation of the new plugin's version zero record
if [ -z "${PLUGIN_STAGE}" ];
then
    VER_ZERO_JSON='{"id": {"S": "'"${PLUGIN_ID}"'"}, "item_version": {"S": "000000"} , "revisions": {"N": "0"} }'
else
    # If plugin_stage has been supplied set it in the DB also
    VERSION="000000"${PLUGIN_STAGE}
    VER_ZERO_JSON='{"id": {"S": "'"${PLUGIN_ID}"'"}, "item_version": {"S": "'"${VERSION}"'"} , "stage": {"S": "'"${PLUGIN_STAGE}"'"}, "revisions": {"N": "0"} }'
fi

# Create plugin version zero record
aws dynamodb put-item \
    --table-name "$TABLE_NAME" \
    --item "$VER_ZERO_JSON" \

# JSON reprsentation of the new plugin's metadata record
VERSION="metadata${PLUGIN_STAGE}"
METADATA_JSON='{"id": {"S": "'"${PLUGIN_ID}"'"}, "item_version": {"S": "'"${VERSION}"'"} , "secret": {"S": "'"$SECRET_HASH"'"} }'

# Create plugin metadata record
aws dynamodb put-item \
    --table-name "$TABLE_NAME" \
    --item "$METADATA_JSON" \

echo secret="$SECRET" hash="$SECRET_HASH"
