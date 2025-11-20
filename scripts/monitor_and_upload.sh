#!/usr/bin/env bash
# Monitor PDF conversion progress and auto-upload when complete

JSONL_FILE="/home/chakri/Documents/Projects/legit-search/data/bulk_index.jsonl"
TARGET_DOCS=26687
INDEX_NAME="legit_search_index"

echo "📊 Monitoring PDF → JSONL conversion..."
echo "Target: $TARGET_DOCS documents"
echo ""

while true; do
    if [ -f "$JSONL_FILE" ]; then
        LINES=$(wc -l < "$JSONL_FILE")
        DOCS=$((LINES / 2))
        SIZE=$(du -h "$JSONL_FILE" | cut -f1)
        PERCENT=$((DOCS * 100 / TARGET_DOCS))
        
        echo -ne "\r📝 Progress: $DOCS / $TARGET_DOCS documents ($PERCENT%) | Size: $SIZE    "
        
        # Check if conversion is complete (no more changes for 10 seconds)
        PREV_LINES=$LINES
        sleep 10
        CURR_LINES=$(wc -l < "$JSONL_FILE" 2>/dev/null || echo "0")
        
        if [ "$CURR_LINES" = "$PREV_LINES" ] && [ "$DOCS" -gt 100 ]; then
            echo -e "\n\n✅ Conversion appears complete: $DOCS documents"
            
            read -p "Upload to Elasticsearch now? (y/n) " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "🚀 Starting bulk upload..."
                bash /home/chakri/Documents/Projects/legit-search/scripts/2_bulk_upload.sh "$JSONL_FILE" "$INDEX_NAME"
                
                echo ""
                echo "📊 Verifying index count..."
                curl -sS "http://localhost:9200/$INDEX_NAME/_count" | jq
                
                echo ""
                echo "✅ Done! Test search: http://localhost:3000"
            fi
            break
        fi
    else
        echo "⏳ Waiting for conversion to start..."
        sleep 5
    fi
done
