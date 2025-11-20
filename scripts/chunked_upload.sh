#!/bin/bash
# Upload in proper chunks

BULK_FILE="data/bulk_index.jsonl"
CHUNK_SIZE=10000  # 5000 documents per chunk
TEMP_DIR="/tmp/es_upload_$$"

echo "============================================================"
echo "  Uploading 26,688 documents in chunks"
echo "============================================================"

mkdir -p "$TEMP_DIR"

# Split file
echo "📦 Splitting file..."
split -l "$CHUNK_SIZE" "$BULK_FILE" "$TEMP_DIR/chunk_"

TOTAL_CHUNKS=$(ls -1 "$TEMP_DIR"/chunk_* 2>/dev/null | wc -l)
echo "✅ Created $TOTAL_CHUNKS chunks"
echo ""

# Upload each chunk
UPLOADED=0
FAILED=0
CURRENT=0

for chunk in "$TEMP_DIR"/chunk_*; do
    CURRENT=$((CURRENT + 1))
    echo -ne "📤 Chunk $CURRENT/$TOTAL_CHUNKS... "
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "http://localhost:9200/_bulk" \
        -H 'Content-Type: application/x-ndjson' \
        --data-binary @"$chunk")
    
    if [ "$HTTP_CODE" = "200" ]; then
        DOCS=$((CHUNK_SIZE / 2))
        UPLOADED=$((UPLOADED + DOCS))
        echo "✅ OK ($UPLOADED total)"
    else
        echo "❌ Failed (HTTP $HTTP_CODE)"
        FAILED=$((FAILED + 1))
    fi
    
    sleep 0.3
done

# Cleanup
rm -rf "$TEMP_DIR"

# Final count
echo ""
curl -s -X POST "http://localhost:9200/legit_search_index/_refresh" > /dev/null
FINAL=$(curl -s "http://localhost:9200/legit_search_index/_count" | jq -r '.count')

echo "============================================================"
echo "  ✅ UPLOAD COMPLETE!"
echo "============================================================"
echo "Uploaded: ~$UPLOADED documents"
echo "Failed chunks: $FAILED"
echo "Final count: $FINAL"
echo ""
