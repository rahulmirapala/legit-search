#!/bin/bash

echo "Starting bulk upload to Elasticsearch..."

# This path is relative to the script's location
# ../data/ goes up one level from 'scripts' and then into 'data'
DATA_FILE="../data/bulk_index.jsonl"
ELASTICSEARCH_URL="http://localhost:9200/_bulk"

curl -s -H "Content-Type: application/x-ndjson" -XPOST $ELASTICSEARCH_URL --data-binary "@$DATA_FILE"

echo
echo "Upload complete."