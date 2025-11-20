#!/bin/bash
# Split and upload bulk data in chunks

BULK_FILE="data/bulk_index.jsonl"
CHUNK_SIZE=5000  # lines (2500 documents)
ES_URL="http://localhost:9200/_bulk"

echo "======================================================================"
echo "  BULK UPLOAD: Splitting and uploading 53K+ documents"
echo "======================================================================"
echo ""

# Count total lines
TOTAL_LINES=$(wc -l < "$BULK_FILE")
TOTAL_DOCS=$((TOTAL_LINES / 2))

echo "📁 Source file: $BULK_FILE"
echo "📊 Total documents: $TOTAL_DOCS"
echo "📦 Chunk size: $((CHUNK_SIZE / 2)) documents per batch"
echo ""

# Create temp directory
TMP_DIR="/tmp/bulk_upload_$$"
mkdir -p "$TMP_DIR"

echo "⏳ Splitting file into chunks..."
split -l "$CHUNK_SIZE" "$BULK_FILE" "$TMP_DIR/chunk_"

CHUNKS=$(ls -1 "$TMP_DIR"/chunk_* | wc -l)
echo "✅ Created $CHUNKS chunks"
echo ""

# Upload each chunk
UPLOADED=0
CHUNK_NUM=0

for chunk in "$TMP_DIR"/chunk_*; do
    CHUNK_NUM=$((CHUNK_NUM + 1))
    
    echo -ne "📤 Uploading chunk $CHUNK_NUM/$CHUNKS... "
    
    RESPONSE=$(curl -s -X POST "$ES_URL" \
        -H 'Content-Type: application/x-ndjson' \
        --data-binary @"$chunk")
    
    # Count successful uploads
    SUCCESS=$(echo "$RESPONSE" | jq -r '.items | length' 2>/dev/null || echo "0")
    UPLOADED=$((UPLOADED + SUCCESS))
    
    echo "✅ $SUCCESS docs (Total: $UPLOADED)"
    
    # Small delay to not overwhelm ES
    sleep 0.5
done

echo ""
echo "🧹 Cleaning up temporary files..."
rm -rf "$TMP_DIR"

echo ""
echo "======================================================================"
echo "  UPLOAD COMPLETE!"
echo "======================================================================"
echo "✅ Uploaded: $UPLOADED documents"
echo ""

# Verify final count
echo "🔄 Refreshing index..."
curl -s -X POST "http://localhost:9200/legit_search_index/_refresh" > /dev/null

FINAL_COUNT=$(curl -s "http://localhost:9200/legit_search_index/_count" | jq -r '.count')
echo "📊 Final document count: $FINAL_COUNT"
echo ""
