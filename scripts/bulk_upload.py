#!/usr/bin/env python3
"""Bulk upload script with progress tracking"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import json
from app.config import Settings

def read_bulk_file(filename):
    """Read bulk file and yield documents"""
    with open(filename, 'r') as f:
        while True:
            # Read action line (index command)
            action_line = f.readline()
            if not action_line:
                break
            
            # Read document line
            doc_line = f.readline()
            if not doc_line:
                break
            
            action = json.loads(action_line)
            doc = json.loads(doc_line)
            
            yield {
                '_index': action['index']['_index'],
                '_source': doc
            }

def main():
    settings = Settings()
    es = Elasticsearch(settings.es_host, request_timeout=120)
    
    print("=" * 60)
    print("  BULK UPLOAD: 53K+ Documents")
    print("=" * 60)
    print()
    
    # Check connection
    if not es.ping():
        print("❌ ERROR: Cannot connect to Elasticsearch")
        sys.exit(1)
    
    bulk_file = 'data/bulk_index.jsonl'
    
    print(f"📁 Reading from: {bulk_file}")
    print("⏳ This will take a few minutes...")
    print()
    
    # Upload in batches
    batch_size = 500
    total_success = 0
    total_failed = 0
    
    actions = []
    for doc in read_bulk_file(bulk_file):
        actions.append(doc)
        
        if len(actions) >= batch_size:
            try:
                success, failed = bulk(es, actions, stats_only=True, raise_on_error=False, request_timeout=60)
                total_success += success
                total_failed += failed
                print(f"✓ Uploaded {total_success:,} documents ({failed} failed)...", end='\r')
                actions = []
            except Exception as e:
                print(f"\n❌ Error: {e}")
                total_failed += len(actions)
                actions = []
    
    # Upload remaining
    if actions:
        try:
            success, failed = bulk(es, actions, stats_only=True, raise_on_error=False, request_timeout=60)
            total_success += success
            total_failed += failed
        except Exception as e:
            print(f"\n❌ Error uploading final batch: {e}")
            total_failed += len(actions)
    
    print()
    print()
    print("=" * 60)
    print("  UPLOAD COMPLETE!")
    print("=" * 60)
    print(f"✅ Successfully uploaded: {total_success:,} documents")
    if total_failed > 0:
        print(f"⚠️  Failed: {total_failed} documents")
    print()
    
    # Verify
    es.indices.refresh(index=settings.index_name)
    count = es.count(index=settings.index_name)['count']
    print(f"📊 Total documents in index: {count:,}")
    print()

if __name__ == "__main__":
    main()
