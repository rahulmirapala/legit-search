#!/usr/bin/env bash
# Complete ingestion pipeline: Download → Convert → Upload → Embeddings
# Usage: bash scripts/ingest_pipeline.sh [year_start] [year_end] [max_per_year]

set -e  # Exit on error

# Default parameters
YEAR_START=${1:-2023}
YEAR_END=${2:-2024}
MAX_PER_YEAR=${3:-20}
OUTPUT_DIR="data/supreme_court_judgments"
JSONL_FILE="data/judgments.jsonl"
INDEX_NAME="legal_judgments"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   Legal Search Complete Ingestion Pipeline               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  Years: $YEAR_START to $YEAR_END"
echo "  Max per year: $MAX_PER_YEAR"
echo "  Output directory: $OUTPUT_DIR"
echo "  JSONL file: $JSONL_FILE"
echo "  Elasticsearch index: $INDEX_NAME"
echo ""

# Step 1: Download judgments from Indian Kanoon
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Downloading judgments from Indian Kanoon"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python scripts/download_indiankanoon.py \
    --year-start "$YEAR_START" \
    --year-end "$YEAR_END" \
    --max-per-year "$MAX_PER_YEAR" \
    --output-dir "$OUTPUT_DIR"

if [ $? -ne 0 ]; then
    echo "❌ Download failed!"
    exit 1
fi

echo ""
echo "✅ Download complete!"
echo ""

# Step 2: Convert to JSONL
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Converting .txt files to JSONL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python scripts/2_txt_to_jsonl.py \
    --input "$OUTPUT_DIR" \
    --output "$JSONL_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Conversion failed!"
    exit 1
fi

echo ""
echo "✅ Conversion complete!"
echo ""

# Step 3: Upload to Elasticsearch
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Uploading to Elasticsearch"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

bash scripts/2_bulk_upload.sh "$JSONL_FILE" "$INDEX_NAME"

if [ $? -ne 0 ]; then
    echo "❌ Upload failed!"
    exit 1
fi

echo ""
echo "✅ Upload complete!"
echo ""

# Step 4: Generate embeddings (optional)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4: Generate embeddings (optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

read -p "Generate semantic embeddings? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python scripts/add_embeddings.py
    echo "✅ Embeddings generated!"
else
    echo "⏭️  Skipping embeddings"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              ✨ PIPELINE COMPLETE ✨                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Summary:"
echo "  • Downloaded judgments from Indian Kanoon"
echo "  • Converted to JSONL format"
echo "  • Uploaded to Elasticsearch index: $INDEX_NAME"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  • Generated semantic embeddings"
fi
echo ""
echo "Your search system is ready! Open http://localhost:3000"
echo ""
