"""Add semantic embeddings to existing documents in Elasticsearch."""
import sys
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan, bulk
from app.config import get_settings
from app.semantic import embed_texts, is_available

def add_embeddings(batch_size=100):
    """Generate and add embeddings to all documents."""
    if not is_available():
        print("Error: Sentence-transformers not available. Install with: pip install sentence-transformers")
        return
    
    settings = get_settings()
    es = Elasticsearch(settings.es_host)
    index = settings.index_name
    
    if not es.indices.exists(index=index):
        print(f"Error: Index '{index}' does not exist.")
        return
    
    print(f"Scanning documents from '{index}'...")
    docs = []
    doc_ids = []
    
    # Collect all documents
    for hit in scan(es, index=index, query={"query": {"match_all": {}}}):
        doc_id = hit['_id']
        source = hit['_source']
        
        # Skip if already has embedding
        if 'embedding' in source:
            continue
        
        # Combine case_name and snippet of full_text for embedding
        text = source.get('case_name', '')
        full_text = source.get('full_text', '')
        if full_text:
            # Use first 512 chars for efficiency
            text += " " + full_text[:512]
        
        docs.append(text)
        doc_ids.append(doc_id)
    
    if not docs:
        print("No documents need embeddings.")
        return
    
    print(f"Generating embeddings for {len(docs)} documents...")
    
    # Process in batches
    actions = []
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i:i+batch_size]
        batch_ids = doc_ids[i:i+batch_size]
        
        embeddings = embed_texts(batch_docs)
        
        for doc_id, embedding in zip(batch_ids, embeddings):
            actions.append({
                '_op_type': 'update',
                '_index': index,
                '_id': doc_id,
                'doc': {'embedding': embedding}
            })
        
        print(f"Processed {min(i+batch_size, len(docs))}/{len(docs)} documents...")
    
    # Bulk update
    print("Uploading embeddings to Elasticsearch...")
    success, failed = bulk(es, actions, raise_on_error=False)
    print(f"Successfully updated {success} documents.")
    if failed:
        print(f"Failed to update {len(failed)} documents.")

if __name__ == "__main__":
    add_embeddings()
