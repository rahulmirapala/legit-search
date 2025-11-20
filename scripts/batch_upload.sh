#!/usr/bin/env bash
# Upload large JSONL files to Elasticsearch in batches

INPUT_FILE="${1:-data/bulk_index.jsonl}"
BATCH_SIZE=1000  # 500 documents per batch
ES_URL="http://localhost:9200/_bulk"

if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ File not found: $INPUT_FILE"
    exit 1
fi

TOTAL_LINES=$(wc -l < "$INPUT_FILE")
TOTAL_DOCS=$((TOTAL_LINES / 2))

echo "📊 Starting batch upload..."
echo "📂 File: $INPUT_FILE"
echo "📝 Total documents: $TOTAL_DOCS"
echo "📦 Batch size: $((BATCH_SIZE / 2)) documents"
echo ""

CURRENT_LINE=0
BATCH_NUM=1
SUCCESS_COUNT=0
ERROR_COUNT=0

while [ $CURRENT_LINE -lt $TOTAL_LINES ]; do
    START_LINE=$((CURRENT_LINE + 1))
    END_LINE=$((CURRENT_LINE + BATCH_SIZE))
    
    if [ $END_LINE -gt $TOTAL_LINES ]; then
        END_LINE=$TOTAL_LINES
    fi
    
    BATCH_DOCS=$(((END_LINE - START_LINE + 1) / 2))
    
    echo -n "📦 Batch $BATCH_NUM: uploading $BATCH_DOCS documents (lines $START_LINE-$END_LINE)... "
    
    # Extract batch and upload
    sed -n "${START_LINE},${END_LINE}p" "$INPUT_FILE" > /tmp/batch_$BATCH_NUM.jsonl
    
    RESPONSE=$(curl -s -X POST "$ES_URL" -H "Content-Type: application/x-ndjson" --data-binary "@/tmp/batch_$BATCH_NUM.jsonl")
    
    ERRORS=$(echo "$RESPONSE" | jq -r '.errors')
    TOOK=$(echo "$RESPONSE" | jq -r '.took')
    
    if [ "$ERRORS" = "false" ]; then
        echo "✅ Success (${TOOK}ms)"
        SUCCESS_COUNT=$((SUCCESS_COUNT + BATCH_DOCS))
    else
        echo "❌ Errors detected"
        ERROR_COUNT=$((ERROR_COUNT + BATCH_DOCS))
        echo "$RESPONSE" | jq '.items[] | select(.index.error) | .index.error' | head -5
    fi
    
    rm /tmp/batch_$BATCH_NUM.jsonl
    
    CURRENT_LINE=$END_LINE
    BATCH_NUM=$((BATCH_NUM + 1))
    
    # Small delay to avoid overwhelming ES
    sleep 0.5
done

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                 UPLOAD COMPLETE                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo "✅ Successfully uploaded: $SUCCESS_COUNT documents"
echo "❌ Failed: $ERROR_COUNT documents"
echo ""
echo "📊 Verifying index count..."
curl -sS "http://localhost:9200/legit_search_index/_count" | jq
