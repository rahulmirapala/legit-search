from fastapi import FastAPI, HTTPException, Query
from elasticsearch import Elasticsearch
from . import search  # Use relative import
from typing import Optional

app = FastAPI(
    title="Legit Search API",
    description="API for searching Indian Supreme Court judgments."
)

# --- Elasticsearch Connection ---
try:
    es = Elasticsearch(
        "http://localhost:9200",
        request_timeout=10, max_retries=3, retry_on_timeout=True
    )
    if not es.ping():
        raise ConnectionError("Could not connect to Elasticsearch.")
    print("Successfully connected to Elasticsearch.")
except Exception as e:
    print(f"Error connecting to Elasticsearch: {e}")
    es = None

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to Legit Search API"}

@app.get("/search")
def search_judgments(
    q: str, 
    title_boost: Optional[float] = Query(3.0, ge=1.0)
):
    """
    Main search endpoint.
    Takes a query 'q' and returns search results.
    Allows an optional 'title_boost' parameter (default: 3.0, min: 1.0)
    """
    if not es or not es.ping():
        raise HTTPException(status_code=503, detail="Search service is unavailable.")

    # 1. Correct the user's query
    try:
        corrected_query = search.autospell(q)
    except Exception as e:
        print(f"Autospell error: {e}")
        corrected_query = q

    # 2. Build the Elasticsearch query, passing the dynamic boost
    query_body = search.build_search_query(corrected_query, title_boost=title_boost)

    # 3. Send query to Elasticsearch
    try:
        response = es.search(index="legit_search_index", body=query_body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search query failed: {e}")

    # 4. Format and return the response
    hits = response['hits']['hits']
    formatted_hits = []
    for hit in hits:
        formatted_hits.append({
            "score": hit['_score'],
            "case_name": hit['_source'].get('case_name'),
            "judgment_date": hit['_source'].get('judgment_date'),
            "citation_id": hit['_source'].get('citation_id'),
            "year": hit['_source'].get('year'),
            "highlights": hit.get('highlight', {}).get('full_text', [])
        })

    return {
        "original_query": q,
        "corrected_query": corrected_query,
        "title_boost_used": title_boost,
        "total_hits": response['hits']['total']['value'],
        "results": formatted_hits
    }