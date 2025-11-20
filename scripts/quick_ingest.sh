#!/bin/bash
# Quick data collection and ingestion script

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   LegitSearch - Data Collection & Ingestion Pipeline     ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Setup paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_BIN="/home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python"

cd "$PROJECT_ROOT"

# Step 1: Download data (optional - comment out if you already have data)
echo "Step 1: Download Supreme Court judgments from Indian Kanoon"
echo "-----------------------------------------------------------"
read -p "Download new data? (y/n, default: n): " download_choice
if [ "$download_choice" = "y" ]; then
    read -p "Start year (default: 2022): " year_start
    year_start=${year_start:-2022}
    
    read -p "End year (default: 2024): " year_end
    year_end=${year_end:-2024}
    
    read -p "Max cases per year (default: 50): " max_per_year
    max_per_year=${max_per_year:-50}
    
    echo "Downloading judgments from Indian Kanoon..."
    $PYTHON_BIN scripts/download_indiankanoon.py \
        --year-start $year_start \
        --year-end $year_end \
        --max-per-year $max_per_year
    
    echo "✓ Download complete!"
else
    echo "⊗ Skipping download - using existing data"
fi

echo ""
echo "Step 2: Convert text files to JSONL format"
echo "-----------------------------------------------------------"
read -p "Process files into JSONL? (y/n, default: y): " process_choice
if [ "$process_choice" != "n" ]; then
    # Check if we need to adapt the script for .txt files instead of .pdf
    echo "Note: Your downloaded files are .txt format"
    echo "Creating adapted processor..."
    
    # Create temporary adapted script
    cat > /tmp/process_text_to_jsonl.py << 'EOF'
import os
import json
import re
from datetime import datetime

def extract_metadata_from_file(filepath, filename):
    """Extract metadata from text file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    case_name = "Unknown Case"
    citation = "Unknown Citation"
    year = None
    judgment_date = None
    full_text = ""
    
    # Parse header metadata
    for i, line in enumerate(lines[:20]):
        if line.startswith("Case:"):
            case_name = line.replace("Case:", "").strip()
        elif line.startswith("Citation:"):
            citation = line.replace("Citation:", "").strip()
        elif line.startswith("Year:"):
            year = int(line.replace("Year:", "").strip())
        elif i > 10:
            # Start collecting full text after header
            full_text = "".join(lines[i:])
            break
    
    # Extract date from filename if available
    date_match = re.search(r'on_(\d{1,2})_([A-Za-z]+)_(\d{4})', filename)
    if date_match:
        try:
            dt = datetime.strptime(f"{date_match.group(1)} {date_match.group(2)} {date_match.group(3)}", "%d %B %Y")
            judgment_date = dt.strftime('%Y-%m-%d')
        except:
            pass
    
    return {
        "case_name": case_name,
        "citation_id": citation,
        "year": year,
        "judgment_date": judgment_date,
        "court": "Supreme Court of India",
        "full_text": full_text.strip()
    }

def main():
    root_dir = "data/supreme_court_judgments"
    output_file = "data/bulk_index.jsonl"
    
    os.makedirs("data", exist_ok=True)
    
    doc_count = 0
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for year_folder in sorted(os.listdir(root_dir)):
            year_path = os.path.join(root_dir, year_folder)
            
            if os.path.isdir(year_path):
                print(f"Processing folder: {year_folder}")
                for filename in os.listdir(year_path):
                    if filename.endswith(".txt") and not filename.endswith("_meta.json"):
                        filepath = os.path.join(year_path, filename)
                        
                        try:
                            doc_data = extract_metadata_from_file(filepath, filename)
                            
                            # Write bulk format
                            f_out.write(json.dumps({"index": {"_index": "legit_search_index"}}) + "\n")
                            f_out.write(json.dumps(doc_data) + "\n")
                            
                            doc_count += 1
                            if doc_count % 50 == 0:
                                print(f"  Processed {doc_count} documents...")
                        
                        except Exception as e:
                            print(f"  Error processing {filename}: {e}")
    
    print(f"\n✓ Total documents processed: {doc_count}")
    print(f"✓ Bulk file created: {output_file}")

if __name__ == "__main__":
    main()
EOF
    
    echo "Converting text files to JSONL..."
    PYTHONPATH="$PROJECT_ROOT" $PYTHON_BIN /tmp/process_text_to_jsonl.py
    
    echo "✓ Conversion complete!"
else
    echo "⊗ Skipping JSONL conversion"
fi

echo ""
echo "Step 3: Upload to Elasticsearch"
echo "-----------------------------------------------------------"
read -p "Upload data to Elasticsearch? (y/n, default: y): " upload_choice
if [ "$upload_choice" != "n" ]; then
    if [ ! -f "data/bulk_index.jsonl" ]; then
        echo "✗ Error: data/bulk_index.jsonl not found!"
        echo "  Please run Step 2 first."
        exit 1
    fi
    
    echo "Uploading to Elasticsearch..."
    curl -s -H "Content-Type: application/x-ndjson" \
         -XPOST "http://localhost:9200/_bulk" \
         --data-binary "@data/bulk_index.jsonl" | \
         $PYTHON_BIN -c "import sys, json; d=json.load(sys.stdin); print(f\"✓ Indexed: {d.get('items', []).__len__()} documents\"); print(f\"  Errors: {d.get('errors', False)}\")"
    
    echo "✓ Upload complete!"
else
    echo "⊗ Skipping Elasticsearch upload"
fi

echo ""
echo "Step 4: Generate semantic embeddings (optional)"
echo "-----------------------------------------------------------"
read -p "Generate embeddings for semantic search? (y/n, default: n): " embed_choice
if [ "$embed_choice" = "y" ]; then
    echo "Generating embeddings (this may take a while)..."
    PYTHONPATH="$PROJECT_ROOT" $PYTHON_BIN scripts/add_embeddings.py
    echo "✓ Embeddings generated!"
else
    echo "⊗ Skipping embeddings - you can run this later"
    echo "  Command: python scripts/add_embeddings.py"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                 Pipeline Complete! ✓                      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Your search index is ready!"
echo ""
echo "Quick check:"
echo "  curl 'http://localhost:8000/search?q=fundamental+rights'"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000/docs"
echo ""
