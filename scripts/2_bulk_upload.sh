#!/bin/bash

# Usage: bash scripts/2_bulk_upload.sh <jsonl_file> [index_name]
# Example: bash scripts/2_bulk_upload.sh data/judgments.jsonl legal_judgments

DATA_FILE="${1:-../data/bulk_index.jsonl}"
INDEX_NAME="${2:-legal_judgments}"
ELASTICSEARCH_URL="http://localhost:9200/_bulk"

if [ ! -f "$DATA_FILE" ]; then
    echo "❌ Error: File not found: $DATA_FILE"
    echo "Usage: bash scripts/2_bulk_upload.sh <jsonl_file> [index_name]"
    exit 1
fi

echo "Starting bulk upload to Elasticsearch..."
echo "📂 File: $DATA_FILE"
echo "📊 Index: $INDEX_NAME"
echo "🔗 Elasticsearch: $ELASTICSEARCH_URL"
echo ""

curl -s -H "Content-Type: application/x-ndjson" -XPOST "$ELASTICSEARCH_URL" --data-binary "@$DATA_FILE"

echo ""
echo "✅ Upload complete."