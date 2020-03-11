#!/bin/sh

# Usage:
# ./new_plugin_record.sh -t '<dynamodb table>' -p <plugin_id> -s

TABLE_NAME=""
PLUGIN_ID=""
PLUGIN_STAGE=""
VER_ZERO_JSON="{}"
METADATA_JSON="{}"
SECRET=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)

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
    -ps|--plugin-stage) #TODO// validation. must be one of dev or prd
    PLUGIN_STAGE="$2"
    shift
    ;;
esac
shift
done

# JSON reprsentation of the new plugin's version zero record
# VER_ZERO_JSON=$(cat <<EOF
# {"id": {"S": "${PLUGIN_ID}"}, "item_version": {"S": "000000-${PLUGIN_STAGE}"} , "stage": {"S": "${PLUGIN_STAGE}"} , "revisions": {"N": "0"} }
# EOF
# )


VER_ZERO_JSON=$(cat <<EOF
{"id": {"S": "${PLUGIN_ID}"}, "item_version": {"S": "000000"} , "revisions": {"N": "0"} }
EOF
)

# Create plugin version zero record
aws dynamodb put-item \
    --table-name "$TABLE_NAME" \
    --item "$VER_ZERO_JSON" \

# JSON reprsentation of the new plugin's metadata record

# METADATA_JSON=$(cat <<EOF
# {"id": {"S": "$PLUGIN_ID"}, "item_version": {"S": "metadata-${PLUGIN_STAGE}"} , "secret": {"S": "$SECRET"} }
# EOF
# )

METADATA_JSON=$(cat <<EOF
{"id": {"S": "$PLUGIN_ID"}, "item_version": {"S": "metadata"} , "secret": {"S": "$SECRET"} }
EOF
)


# Create plugin metadata record
aws dynamodb put-item \
    --table-name "$TABLE_NAME" \
    --item "$METADATA_JSON" \

echo secret="$SECRET"