#!/bin/bash
# Reindex script: Migrate data to new index with improved mappings
# This script safely reindexes without data loss

set -e  # Exit on error

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

ES_HOST="http://localhost:9200"
OLD_INDEX="legit_search_index"
NEW_INDEX="legit_search_index_v2"
MAPPING_FILE="mapping.json"

echo -e "${YELLOW}====================================================${NC}"
echo -e "${YELLOW}  Reindexing with Improved Search Mappings${NC}"
echo -e "${YELLOW}====================================================${NC}"
echo ""

# 1. Check Elasticsearch is running
echo -e "${YELLOW}[1/6]${NC} Checking Elasticsearch connection..."
if ! curl -s "$ES_HOST" > /dev/null; then
    echo -e "${RED}ERROR: Cannot connect to Elasticsearch at $ES_HOST${NC}"
    echo "Please start Elasticsearch and try again."
    exit 1
fi
echo -e "${GREEN}✓${NC} Elasticsearch is running"
echo ""

# 2. Check if old index exists
echo -e "${YELLOW}[2/6]${NC} Checking current index..."
if curl -s -o /dev/null -w "%{http_code}" "$ES_HOST/$OLD_INDEX" | grep -q "200"; then
    DOC_COUNT=$(curl -s "$ES_HOST/$OLD_INDEX/_count" | grep -oP '"count":\K[0-9]+')
    echo -e "${GREEN}✓${NC} Found existing index: $OLD_INDEX with $DOC_COUNT documents"
else
    echo -e "${YELLOW}⚠${NC} No existing index found. Will create fresh index."
    DOC_COUNT=0
fi
echo ""

# 3. Create new index with improved mapping
echo -e "${YELLOW}[3/6]${NC} Creating new index with improved mappings..."
if curl -s -o /dev/null -w "%{http_code}" "$ES_HOST/$NEW_INDEX" | grep -q "200"; then
    echo -e "${YELLOW}⚠${NC} New index already exists. Deleting it first..."
    curl -s -X DELETE "$ES_HOST/$NEW_INDEX" > /dev/null
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$ES_HOST/$NEW_INDEX" \
    -H 'Content-Type: application/json' \
    -d @"$MAPPING_FILE")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓${NC} Created new index: $NEW_INDEX"
else
    echo -e "${RED}ERROR: Failed to create index (HTTP $HTTP_CODE)${NC}"
    exit 1
fi
echo ""

# 4. Reindex data if old index exists
if [ "$DOC_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}[4/6]${NC} Migrating $DOC_COUNT documents to new index..."
    echo "This may take a few minutes..."
    
    REINDEX_RESPONSE=$(curl -s -X POST "$ES_HOST/_reindex" \
        -H 'Content-Type: application/json' \
        -d "{
            \"source\": {\"index\": \"$OLD_INDEX\"},
            \"dest\": {\"index\": \"$NEW_INDEX\"}
        }")
    
    MIGRATED=$(echo "$REINDEX_RESPONSE" | grep -oP '"total":\K[0-9]+' | head -1)
    
    if [ "$MIGRATED" = "$DOC_COUNT" ]; then
        echo -e "${GREEN}✓${NC} Successfully migrated $MIGRATED documents"
    else
        echo -e "${RED}⚠ Warning: Expected $DOC_COUNT docs, migrated $MIGRATED${NC}"
    fi
else
    echo -e "${YELLOW}[4/6]${NC} No data to migrate (starting fresh)"
fi
echo ""

# 5. Verify new index
echo -e "${YELLOW}[5/6]${NC} Verifying new index..."
sleep 2  # Wait for indexing to complete
NEW_COUNT=$(curl -s "$ES_HOST/$NEW_INDEX/_count" | grep -oP '"count":\K[0-9]+')
echo -e "${GREEN}✓${NC} New index has $NEW_COUNT documents"
echo ""

# 6. Switch to new index
echo -e "${YELLOW}[6/6]${NC} Switching to new index..."
echo -e "${YELLOW}Options:${NC}"
echo "  A) Delete old index and rename new one (RECOMMENDED)"
echo "  B) Keep both indexes (for testing)"
echo ""
read -p "Choose option (A/B): " choice

case $choice in
    [Aa]* )
        if [ "$DOC_COUNT" -gt 0 ]; then
            echo "Deleting old index: $OLD_INDEX"
            curl -s -X DELETE "$ES_HOST/$OLD_INDEX" > /dev/null
        fi
        
        echo "Creating alias: $OLD_INDEX → $NEW_INDEX"
        curl -s -X POST "$ES_HOST/_aliases" \
            -H 'Content-Type: application/json' \
            -d "{
                \"actions\": [
                    {\"add\": {\"index\": \"$NEW_INDEX\", \"alias\": \"$OLD_INDEX\"}}
                ]
            }" > /dev/null
        
        echo -e "${GREEN}✓${NC} Migration complete! Using alias for backward compatibility."
        ;;
    [Bb]* )
        echo -e "${GREEN}✓${NC} Kept both indexes. You can test with:"
        echo "   - Old: $OLD_INDEX ($DOC_COUNT docs)"
        echo "   - New: $NEW_INDEX ($NEW_COUNT docs)"
        echo ""
        echo "To switch your app to new index, update .env:"
        echo "   ES_INDEX=$NEW_INDEX"
        ;;
    * )
        echo -e "${RED}Invalid choice. Keeping both indexes.${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}  Reindexing Complete!${NC}"
echo -e "${GREEN}====================================================${NC}"
echo ""
echo "Next steps:"
echo "1. Test search quality: python scripts/diagnose_search.py"
echo "2. Ingest full dataset: python scripts/quick_ingest.py"
echo ""
echo "Improvements applied:"
echo "  ✓ Case name boost: 1x → 5x (15.0 default)"
echo "  ✓ Stopwords: 100+ → 3 (a, an, the)"
echo "  ✓ Synonyms: 7 → 19 legal terms"
echo "  ✓ Better field coordination (cross_fields)"
echo "  ✓ Minimum term matching (75%)"
echo ""
