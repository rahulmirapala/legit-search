#!/usr/bin/env python3
"""
Convert downloaded .txt judgments from Indian Kanoon to JSONL for Elasticsearch.
Works with output from scripts/download_indiankanoon.py

Usage:
    python scripts/2_txt_to_jsonl.py --input data/supreme_court_judgments --output data/judgments.jsonl
"""

import os
import json
import re
import argparse
from pathlib import Path
from datetime import datetime


def clean_text(text):
    """Clean and normalize text."""
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    # Remove extra newlines
    text = text.replace('\r', ' ').replace('\n', ' ')
    return text.strip()


def convert_date_format(date_str):
    """Convert date from 15_March_2024 to 2024-03-15."""
    if not date_str:
        return None
    try:
        # Parse format like "15_March_2024"
        dt = datetime.strptime(date_str, '%d_%B_%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return None


def parse_txt_file(filepath):
    """Parse a .txt judgment file and extract metadata + content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split header from main text (header ends at the === separator)
        parts = content.split('=' * 80, 1)
        
        metadata = {}
        full_text = content  # Default to full content
        
        if len(parts) == 2:
            header = parts[0]
            full_text = parts[1].strip()
            
            # Parse header lines
            for line in header.split('\n'):
                line = line.strip()
                if line.startswith('Case:'):
                    metadata['case_name'] = line.replace('Case:', '').strip()
                elif line.startswith('Citation:'):
                    metadata['citation_id'] = line.replace('Citation:', '').strip()
                elif line.startswith('Year:'):
                    try:
                        metadata['year'] = int(line.replace('Year:', '').strip())
                    except ValueError:
                        pass
                elif line.startswith('Source:'):
                    metadata['source_url'] = line.replace('Source:', '').strip()
        
        # Try to load companion _meta.json if exists
        meta_file = str(filepath).replace('.txt', '_meta.json')
        if os.path.exists(meta_file):
            with open(meta_file, 'r', encoding='utf-8') as f:
                json_meta = json.load(f)
                # Merge, preferring JSON metadata
                for key in ['case_name', 'citation_id', 'year', 'judgment_date', 'source_url']:
                    if key in json_meta and json_meta[key]:
                        metadata[key] = json_meta[key]
        
        # Clean the full text
        clean_full_text = clean_text(full_text)
        
        # Build final document
        doc = {
            'case_name': metadata.get('case_name', 'Unknown Case'),
            'citation_id': metadata.get('citation_id', 'Unknown Citation'),
            'year': metadata.get('year', 0),
            'judgment_date': convert_date_format(metadata.get('judgment_date')),
            'full_text': clean_full_text,
            'court': 'Supreme Court of India'
        }
        
        return doc
    
    except Exception as e:
        print(f"  ⚠ Error parsing {filepath}: {e}")
        return None


def convert_directory(input_dir, output_file):
    """Convert all .txt files in directory to JSONL."""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return 0
    
    print(f"📂 Scanning: {input_dir}")
    print(f"📝 Output: {output_file}")
    print(f"{'='*60}")
    
    doc_count = 0
    
    with open(output_file, 'w', encoding='utf-8') as out:
        # Walk through year folders
        for year_folder in sorted(input_path.iterdir()):
            if year_folder.is_dir() and year_folder.name.isdigit():
                print(f"\n📁 Processing year: {year_folder.name}")
                
                year_count = 0
                for txt_file in sorted(year_folder.glob('*.txt')):
                    # Skip _meta.json files
                    if txt_file.stem.endswith('_meta'):
                        continue
                    
                    doc = parse_txt_file(txt_file)
                    
                    if doc:
                        # Write JSONL format (index action + document)
                        index_action = {"index": {"_index": "legit_search_index"}}
                        out.write(json.dumps(index_action) + '\n')
                        out.write(json.dumps(doc) + '\n')
                        
                        doc_count += 1
                        year_count += 1
                        
                        if doc_count % 50 == 0:
                            print(f"  ✓ Processed {doc_count} documents...")
                
                print(f"  → {year_count} judgments from {year_folder.name}")
    
    print(f"\n{'='*60}")
    print(f"✅ Conversion complete!")
    print(f"📊 Total documents: {doc_count}")
    print(f"💾 Output file: {output_file}")
    print(f"{'='*60}")
    
    return doc_count


def main():
    parser = argparse.ArgumentParser(
        description='Convert Indian Kanoon .txt judgments to JSONL format'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/supreme_court_judgments',
        help='Input directory containing year folders with .txt files'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/judgments.jsonl',
        help='Output JSONL file path'
    )
    
    args = parser.parse_args()
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║        Indian Kanoon TXT → JSONL Converter                ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    count = convert_directory(args.input, args.output)
    
    if count > 0:
        print(f"\n✨ Next steps:")
        print(f"1. Upload to Elasticsearch:")
        print(f"   bash scripts/2_bulk_upload.sh {args.output} legal_judgments")
        print(f"2. (Optional) Generate embeddings:")
        print(f"   python scripts/add_embeddings.py")
    else:
        print(f"\n⚠ No documents processed. Check input directory.")


if __name__ == '__main__':
    main()
