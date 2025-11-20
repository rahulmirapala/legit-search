#!/usr/bin/env python3
"""Safe reindexing script: Backup → Delete → Recreate → Restore"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, scan
import json
from app.config import Settings

def main():
    settings = Settings()
    es = Elasticsearch(settings.es_host, request_timeout=60)
    index = settings.index_name
    
    print("=" * 60)
    print("  SAFE REINDEXING WITH IMPROVED MAPPINGS")
    print("=" * 60)
    print()
    
    # Step 1: Check connection
    print("[1/5] Checking Elasticsearch connection...")
    if not es.ping():
        print("❌ ERROR: Cannot connect to Elasticsearch")
        sys.exit(1)
    print("✅ Connected")
    print()
    
    # Step 2: Backup existing data
    print("[2/5] Backing up existing data...")
    if not es.indices.exists(index=index):
        print("ℹ️  No existing index found. Creating fresh index.")
        documents = []
    else:
        # Use scan to get all documents
        documents = list(scan(es, index=index, query={"query": {"match_all": {}}}))
        print(f"✅ Backed up {len(documents)} documents")
    print()
    
    # Step 3: Delete old index
    if es.indices.exists(index=index):
        print("[3/5] Deleting old index...")
        es.indices.delete(index=index)
        print("✅ Deleted")
    else:
        print("[3/5] No old index to delete")
    print()
    
    # Step 4: Create new index with improved mapping
    print("[4/5] Creating index with improved mapping...")
    mapping_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mapping.json')
    
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
    
    es.indices.create(index=index, body=mapping)
    print("✅ Created with improved settings:")
    print("   • Case name boost: 1x → 5x (15.0 default)")
    print("   • Stopwords: 100+ → 3 (a, an, the)")
    print("   • Synonyms: 7 → 19 legal terms")
    print("   • Cross-fields coordination")
    print("   • Minimum should match: 75%")
    print()
    
    # Step 5: Restore data
    if documents:
        print("[5/5] Restoring documents...")
        actions = []
        for doc in documents:
            action = {
                '_index': index,
                '_id': doc['_id'],
                '_source': doc['_source']
            }
            actions.append(action)
        
        try:
            success, failed = bulk(es, actions, stats_only=True, raise_on_error=False, request_timeout=60)
            print(f"✅ Restored {success} documents")
            if failed:
                print(f"⚠️  Failed to restore {failed} documents")
        except Exception as e:
            print(f"⚠️  Error during bulk restore: {e}")
            print("   Trying individual inserts...")
            success_count = 0
            for doc in documents:
                try:
                    es.index(index=index, id=doc['_id'], document=doc['_source'])
                    success_count += 1
                except Exception as ie:
                    print(f"   Failed to restore document {doc['_id']}: {ie}")
            print(f"✅ Restored {success_count} documents individually")
    else:
        print("[5/5] No data to restore (fresh index)")
    print()
    
    # Verify
    print("Waiting for index to be ready...")
    import time
    time.sleep(3)
    es.indices.refresh(index=index)
    
    try:
        count = es.count(index=index)['count']
    except Exception:
        count = "unknown (index still initializing)"
    
    print("=" * 60)
    print("  REINDEXING COMPLETE!")
    print("=" * 60)
    print(f"Index: {index}")
    print(f"Documents: {count}")
    print()
    print("Next steps:")
    print("1. Test search: python scripts/diagnose_search.py")
    print("2. Add more data: python scripts/quick_ingest.py")
    print()

if __name__ == "__main__":
    main()
