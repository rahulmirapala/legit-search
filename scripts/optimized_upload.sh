#!/bin/bash

# Optimized bulk upload script - 500 documents per chunk
# This stays well under Elasticsearch's 100MB limit

FILE="data/bulk_index.jsonl"
CHUNK_SIZE=1000  # 1000 lines = 500 documents
ES_URL="http://localhost:9200/_bulk"
TOTAL_LINES=$(wc -l < "$FILE")
TOTAL_CHUNKS=$((($TOTAL_LINES + $CHUNK_SIZE - 1) / $CHUNK_SIZE))

echo "📊 Upload Plan:"
echo "  Total lines: $TOTAL_LINES"
echo "  Chunk size: $CHUNK_SIZE lines (500 documents)"
echo "  Total chunks: $TOTAL_CHUNKS"
echo ""

start_line=1
chunk_num=1

while [ $start_line -le $TOTAL_LINES ]; do
    echo "📦 Chunk $chunk_num/$TOTAL_CHUNKS (lines $start_line-$((start_line + CHUNK_SIZE - 1)))"
    
    # Extract chunk and upload
    sed -n "${start_line},$((start_line + CHUNK_SIZE - 1))p" "$FILE" | \
        curl -s -X POST "$ES_URL" \
        -H 'Content-Type: application/x-ndjson' \
        --data-binary @- \
        -w "\nHTTP: %{http_code}\n" | \
        grep -E "(errors|took|HTTP:)" | head -3
    
    start_line=$((start_line + CHUNK_SIZE))
    chunk_num=$((chunk_num + 1))
    
    # Small delay to prevent overwhelming ES
    sleep 1
done

echo ""
echo "✅ Upload complete!"
echo ""
echo "📈 Checking index stats..."
curl -s "http://localhost:9200/_cat/indices/legit_search_index?v&h=index,docs.count,store.size"
