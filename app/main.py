from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from elasticsearch import Elasticsearch
from typing import Optional
from . import search  # legacy utilities (spell correction kept)
from .config import Settings, get_settings
from .schemas import SearchResponse
from .cache import cache, make_cache_key
from .llm import expand_query_safe, rewrite_query_safe, classify_query_safe
from .logging_config import configure_logging
from .metrics import router as metrics_router, record_metrics_middleware, CACHE_HIT, CACHE_MISS
from .live_ecourts import live_supreme_search  # Live eCourts integration
from .query_understanding import detect_query_type, should_expand, should_use_fuzzy
from .advanced_ranking import rerank_with_learning_to_rank, deduplicate_results
from .query_validation import clean_query
import logging, time, uuid, httpx, pathlib, re
from contextvars import ContextVar

# Context variable for request ID
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

# NOTE: main.py updated to support pagination, highlight toggle, optional query expansion via LLM,
# and improved multi_match based search query building.

app = FastAPI(
    title="Legit Search API",
    description="API for searching Indian Supreme Court judgments (BM25 + optional expansion)."
)

# CORS: allow local frontend dev and any future deployed origins. Adjust as needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

configure_logging(use_json=True)
logger = logging.getLogger("legit-search")
record_metrics_middleware(app)
app.include_router(metrics_router)

# --- Static PDF mount (Supreme Court judgments) ---
PDF_ROOT = (pathlib.Path(__file__).resolve().parent.parent / "data" / "supreme_court_judgments")
if PDF_ROOT.exists():
    # Serves /pdfs/<year>/<filename>.PDF
    app.mount("/pdfs", StaticFiles(directory=str(PDF_ROOT)), name="pdfs")

class RequestIDLogAdapter(logging.LoggerAdapter):
    """Add request ID to log records."""
    def process(self, msg, kwargs):
        request_id = request_id_var.get()
        extra = kwargs.get('extra', {})
        if request_id:
            extra['request_id'] = request_id
        kwargs['extra'] = extra
        return msg, kwargs

# Create logger adapter
logger_adapter = RequestIDLogAdapter(logger, {})

# --- Error Handlers ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error.get("loc", [])),
            "message": error.get("msg", ""),
            "type": error.get("type", "")
        })
    
    logger_adapter.warning("Validation error", extra={"errors": errors, "path": str(request.url.path)})
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid request parameters",
            "details": errors,
            "request_id": request_id_var.get()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    logger_adapter.warning(
        "HTTP exception",
        extra={"status_code": exc.status_code, "detail": exc.detail, "path": str(request.url.path)}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "request_id": request_id_var.get()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger_adapter.error(
        "Unhandled exception",
        extra={"error": str(exc), "type": type(exc).__name__, "path": str(request.url.path)},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": request_id_var.get()
        }
    )

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request."""
    req_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    request_id_var.set(req_id)
    response = await call_next(request)
    response.headers['X-Request-ID'] = req_id
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    logger_adapter.info(
        "HTTP request completed",
        extra={
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "duration_ms": round(duration, 2)
        }
    )
    return response

# --- Elasticsearch Connection ---
def get_es_client(settings: Settings = Depends(get_settings)):
    """Provide a connected Elasticsearch client or raise HTTP 503."""
    try:
        es_client = Elasticsearch(
            settings.es_host,
            request_timeout=10, 
            max_retries=3, 
            retry_on_timeout=True,
            verify_certs=False  # Allow self-signed certs in dev
        )
        if not es_client.ping():
            raise HTTPException(status_code=503, detail="Search backend unavailable.")
        return es_client
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Elasticsearch connection error: {e}")

# --- API Endpoints ---

@app.get("/")
def read_root(settings: Settings = Depends(get_settings)):
    return {"message": "Welcome to Legit Search API", "index": settings.index_name}

@app.get("/health")
def health(es: Elasticsearch = Depends(get_es_client), settings: Settings = Depends(get_settings)):
    """Basic health check for Elasticsearch and index existence."""
    exists = es.indices.exists(index=settings.index_name)
    return {"elasticsearch": "up", "index_exists": bool(exists), "index": settings.index_name}

@app.get("/stats")
def stats(es: Elasticsearch = Depends(get_es_client), settings: Settings = Depends(get_settings)):
    """Return index statistics (docs count, size in bytes)."""
    try:
        data = es.indices.stats(index=settings.index_name)
        prim = data.get('indices', {}).get(settings.index_name, {})
        store_stats = prim.get('primaries', {}).get('store', {})
        docs_stats = prim.get('primaries', {}).get('docs', {})
        return {
            "index": settings.index_name,
            "doc_count": docs_stats.get('count'),
            "store_size_in_bytes": store_stats.get('size_in_bytes'),
            "store_size_human": f"{store_stats.get('size_in_bytes',0)/1024/1024:.2f} MB"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {e}")

@app.get("/aggregations")
def get_aggregations(
    es: Elasticsearch = Depends(get_es_client),
    settings: Settings = Depends(get_settings)
):
    """Get facet aggregations for filtering (year distribution, courts)."""
    try:
        agg_query = {
            "size": 0,
            "aggs": {
                "years": {
                    "terms": {
                        "field": "year",
                        "size": 100,
                        "order": {"_key": "desc"}
                    }
                },
                "courts": {
                    "terms": {
                        "field": "court",
                        "size": 50
                    }
                },
                "year_stats": {
                    "stats": {
                        "field": "year"
                    }
                }
            }
        }
        
        response = es.search(index=settings.index_name, body=agg_query)
        aggs = response.get('aggregations', {})
        
        years = [{"year": b['key'], "count": b['doc_count']} 
                for b in aggs.get('years', {}).get('buckets', [])]
        courts = [{"court": b['key'], "count": b['doc_count']} 
                 for b in aggs.get('courts', {}).get('buckets', [])]
        year_stats = aggs.get('year_stats', {})
        
        return {
            "years": years,
            "courts": courts,
            "year_range": {
                "min": int(year_stats.get('min', 0)) if year_stats.get('min') else None,
                "max": int(year_stats.get('max', 0)) if year_stats.get('max') else None
            },
            "total_documents": response.get('hits', {}).get('total', {}).get('value', 0)
        }
    except Exception as e:
        logger_adapter.error("Aggregations failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Aggregations failed: {e}")

@app.get("/suggest")
def suggest(
    q: str = Query(..., min_length=1, max_length=200, description="Query text for suggestions"),
    limit: int = Query(10, ge=1, le=50),
    fuzzy: bool = Query(True, description="Enable fuzzy matching for typos"),
    include_case_names: bool = Query(True, description="Include case name suggestions"),
    include_legal_terms: bool = Query(True, description="Include legal term suggestions"),
    include_citations: bool = Query(True, description="Include citation suggestions"),
    include_phrases: bool = Query(False, description="Include phrase suggestions"),
    es: Elasticsearch = Depends(get_es_client),
    settings: Settings = Depends(get_settings)
):
    """
    Get advanced autocomplete suggestions with multiple sources.
    
    Features:
    - Case name suggestions with fuzzy matching
    - Legal term suggestions (IPC, constitutional terms, etc.)
    - Citation suggestions (e.g., '2020 SCR', 'AIR 1973')
    - Phrase suggestions from full text
    - Intelligent ranking based on relevance and frequency
    """
    try:
        from app.autocomplete import get_autocomplete_engine
        
        engine = get_autocomplete_engine(es, settings.index_name)
        
        suggestions = engine.get_all_suggestions(
            text=q,
            limit=limit,
            include_case_names=include_case_names,
            include_legal_terms=include_legal_terms,
            include_citations=include_citations,
            include_phrases=include_phrases,
            fuzzy=fuzzy
        )
        
        return {
            "query": q,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggest failed: {e}")

@app.get("/spell")
def spell_check(
    q: str = Query(..., min_length=2, max_length=500, description="Query text to spell check"),
    max_suggestions: int = Query(5, ge=1, le=20),
    es: Elasticsearch = Depends(get_es_client),
    settings: Settings = Depends(get_settings)
):
    """
    Get spelling corrections for query text.
    
    Returns:
    - corrections: List of suggested spelling corrections per word
    - corrected_query: Full corrected query (if corrections found)
    - has_corrections: Boolean indicating if corrections were suggested
    """
    try:
        from app.autocomplete import get_spell_checker
        
        spell_checker = get_spell_checker(es, settings.index_name)
        
        # Get individual word corrections
        corrections = spell_checker.suggest_corrections(q, max_suggestions=max_suggestions)
        
        # Get fully corrected query
        corrected_query = spell_checker.correct_query(q)
        
        return {
            "original_query": q,
            "corrections": corrections,
            "corrected_query": corrected_query,
            "has_corrections": len(corrections) > 0 or corrected_query is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spell check failed: {e}")

@app.get("/search", response_model=SearchResponse)
def search_judgments(
    q: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    title_boost: float = Query(3.0, ge=1.0, le=10.0),
    include_highlights: bool = Query(True),
    expand: bool = Query(False, description="Use LLM to expand query terms if API key configured"),
    spell: bool = Query(True, description="Apply spell correction"),
    mode: str = Query("bm25", description="Search mode: 'bm25', 'hybrid', or 'semantic'"),
    semantic_weight: float = Query(0.3, ge=0.0, le=1.0, description="Weight for semantic in hybrid mode"),
    rerank: bool = Query(False, description="Apply cross-encoder reranking to results"),
    fuzzy: bool = Query(False, description="Enable fuzzy lexical matching"),
    synonyms: bool = Query(False, description="Expand with static legal synonyms"),
    year_from: Optional[int] = Query(None, description="Filter by year (from)"),
    year_to: Optional[int] = Query(None, description="Filter by year (to)"),
    court: Optional[str] = Query(None, description="Filter by court name"),
    search_priority: str = Query("balanced", description="Search priority: 'balanced', 'heading', 'introduction', 'body', or 'conclusion'"),
    min_score: float = Query(0.0, ge=0.0, description="Minimum relevance score threshold"),
    highlight_size: int = Query(150, ge=20, le=1000, description="Highlight fragment size"),
    highlight_fragments: int = Query(3, ge=1, le=10, description="Number of highlight fragments"),
    raw_query: bool = Query(False, description="Include raw Elasticsearch query body in response"),
    es: Elasticsearch = Depends(get_es_client),
    settings: Settings = Depends(get_settings)
):
    """Main search endpoint with pagination, optional LLM expansion, hybrid/semantic search, and reranking."""
    
    # 0. Query validation
    cleaned_q, is_valid, validation_error = clean_query(q)
    if not is_valid:
        logger_adapter.warning("Invalid query", extra={"query": q, "error": validation_error})
        raise HTTPException(status_code=400, detail=validation_error)
    
    # Use cleaned query for all subsequent operations
    q = cleaned_q
    
    # 1. Query understanding and intelligent routing
    query_analysis = detect_query_type(q)
    logger_adapter.info("Query analysis", extra={
        "type": query_analysis['type'],
        "confidence": query_analysis['confidence'],
        "features": query_analysis['features']
    })
    
    # Override expand/fuzzy based on query type if not explicitly set
    if not expand and should_expand(q):
        expand = True
        logger_adapter.info("Auto-enabled expansion based on query type")
    if not fuzzy and should_use_fuzzy(q):
        fuzzy = True
        logger_adapter.info("Auto-enabled fuzzy matching based on query type")
    
    # 2. Spell correction
    corrected_query = q
    if spell:
        try:
            corrected_query = search.autospell(q)
        except Exception:
            corrected_query = q

    # 3. Optional expansion via LLM + static synonyms
    expanded_terms: list[str] = []
    if expand:
        expanded_terms.extend(expand_query_safe(corrected_query))
    if synonyms:
        try:
            from .synonyms import expand_with_synonyms
            expanded_terms.extend(expand_with_synonyms(corrected_query))
        except Exception:
            pass
    # Deduplicate preserving order
    seen = set()
    expanded_terms = [t for t in expanded_terms if not (t in seen or seen.add(t))]

    # 4. Build final query text (basic concatenation of expansion terms)
    final_query_text = corrected_query
    if expanded_terms:
        # Add expanded terms separated by space (could be improved with operators later)
        final_query_text += " " + " ".join(expanded_terms)

    # 5. Caching key
    cache_key = make_cache_key(
        final_query_text, title_boost, page, page_size,
        include_highlights, expand, spell, mode, semantic_weight, rerank, raw_query,
        fuzzy=fuzzy, synonyms=synonyms
    )
    cached = cache.get(cache_key)
    if cached:
        CACHE_HIT.labels("search").inc()
        logger_adapter.info("Cache hit", extra={"cache_key_hash": hash(cache_key) % 10000})
        return cached
    else:
        CACHE_MISS.labels("search").inc()

    # 6. Build ES query body based on mode
    from_offset = (page - 1) * page_size
    
    # Build filters dict
    filters = {}
    if year_from:
        filters['year_from'] = year_from
    if year_to:
        filters['year_to'] = year_to
    if court:
        filters['court'] = court
    
    # Check if semantic mode is requested
    use_semantic = mode in ["hybrid", "semantic"]
    query_vector = None
    
    if use_semantic:
        from .semantic import embed_query, is_available
        if not is_available():
            logger_adapter.warning("Semantic mode requested but embeddings not available, falling back to BM25")
            mode = "bm25"
        else:
            query_vector = embed_query(final_query_text)
            if query_vector is None:
                logger_adapter.warning("Embedding generation returned None; falling back to BM25")
                mode = "bm25"
    
    # Build query based on mode
    if mode == "hybrid" and query_vector:
        query_body = search.build_hybrid_query(
            final_query_text,
            query_vector,
            title_boost=title_boost,
            include_highlights=include_highlights,
            size=page_size,
            from_offset=from_offset,
            semantic_weight=semantic_weight,
            filters=filters if filters else None,
            search_priority=search_priority,
            highlight_size=highlight_size,
            highlight_fragments=highlight_fragments
        )
    elif mode == "semantic" and query_vector:
        # Pure semantic search (100% vector weight)
        query_body = search.build_hybrid_query(
            final_query_text,
            query_vector,
            title_boost=title_boost,
            include_highlights=include_highlights,
            size=page_size,
            from_offset=from_offset,
            semantic_weight=1.0,
            filters=filters if filters else None,
            search_priority=search_priority,
            highlight_size=highlight_size,
            highlight_fragments=highlight_fragments
        )
    else:
        # Default BM25 mode (optionally fuzzy)
        query_body = search.build_multi_match_query(
            final_query_text,
            title_boost=title_boost,
            include_highlights=include_highlights,
            size=page_size,
            from_offset=from_offset,
            filters=filters if filters else None,
            search_priority=search_priority,
            highlight_size=highlight_size,
            highlight_fragments=highlight_fragments,
            fuzzy=fuzzy
        )

    # 7. Execute search
    try:
        response = es.search(index=settings.index_name, body=query_body)
    except Exception as e:
        logger_adapter.error("Search query failed", extra={"error": str(e), "query": final_query_text})
        raise HTTPException(status_code=500, detail=f"Search query failed: {e}")

    hits = response.get('hits', {}).get('hits', [])
    total_value = response.get('hits', {}).get('total', {}).get('value', 0)
    results = []
    for hit in hits:
        # Apply minimum score filter
        if min_score > 0 and hit.get('_score', 0) < min_score:
            continue
            
        src = hit.get('_source', {})
        # Lightweight PDF candidate inference based on first token + year folder
        pdf_candidates = None
        if src.get('year') and src.get('case_name') and PDF_ROOT.exists():
            year_folder = PDF_ROOT / str(src['year'])
            if year_folder.exists():
                first_token = src['case_name'].split()[0].lower().strip('.,()')
                # Match PDFs starting with first token (case-insensitive)
                matches = [f.name for f in year_folder.glob(f"{first_token}*.PDF")]
                if matches:
                    pdf_candidates = [f"{src['year']}/{m}" for m in matches[:8]]
        # Construct deterministic pdf_url if document already stores pdf_filename
        pdf_url = None
        pdf_filename = src.get('pdf_filename')
        if pdf_filename and src.get('year') and PDF_ROOT.exists():
            # Verify file exists before exposing link
            file_path = PDF_ROOT / str(src['year']) / pdf_filename
            if file_path.exists():
                pdf_url = f"/pdfs/{src['year']}/{pdf_filename}"
        # Fallback: if we found candidate filenames above and no explicit pdf_url, expose the first candidate
        if not pdf_url and pdf_candidates:
            first = pdf_candidates[0]
            pdf_url = f"/pdfs/{first}"

        results.append({
            "score": hit.get('_score'),
            "es_id": hit.get('_id'),
            "case_name": src.get('case_name'),
            "judgment_date": src.get('judgment_date'),
            "citation_id": src.get('citation_id'),
            "year": src.get('year'),
            "full_text": src.get('full_text', ''),
            "highlights": hit.get('highlight', {}).get('full_text', []) if include_highlights else [],
            "pdf_candidates": pdf_candidates,
            "pdf_url": pdf_url
        })
    
    # 8. Apply advanced reranking combining multiple signals
    if rerank:
        from .rerank import rerank as apply_rerank, is_available as rerank_available
        if rerank_available():
            logger_adapter.info("Applying cross-encoder reranking", extra={"num_results": len(results)})
            results = apply_rerank(final_query_text, results)
        else:
            logger_adapter.warning("Cross-encoder reranking requested but not available")
    
    # 9. Apply learning-to-rank with multiple signals
    logger_adapter.info("Applying learning-to-rank", extra={"query_type": query_analysis['type']})
    results = rerank_with_learning_to_rank(corrected_query, results, query_analysis)
    
    # 10. Deduplicate near-identical results
    original_count = len(results)
    results = deduplicate_results(results)
    if len(results) < original_count:
        logger_adapter.info("Deduplicated results", extra={"removed": original_count - len(results)})

    payload: SearchResponse = SearchResponse(
        original_query=q,
        corrected_query=corrected_query,
        expanded_terms=expanded_terms,
        final_query=final_query_text,
        title_boost_used=title_boost,
        page=page,
        page_size=page_size,
        total_hits=total_value,
        results=results,
        raw_query=query_body if raw_query else None,
        llm_rewrite=rewrite_query_safe(corrected_query) if expand else None,
        classification=classify_query_safe(corrected_query) if expand else None
    )
    cache.set(cache_key, payload.dict())
    logger_adapter.info("Stored result in cache", extra={"total_hits": total_value, "mode": mode})
    return payload

# --- PDF helper endpoints ---
@app.get("/pdf/search")
def pdf_search(case_name: str = Query(..., description="Case name to match against PDF filenames"),
               year: int | None = Query(None, description="Optional year folder to restrict search")):
    """Find the PDF with the exact same title as the case name.
    Returns the best match or empty list if no good match found.
    """
    if not PDF_ROOT.exists():
        return {"matches": [], "pdf_root_present": False}
    
    # Normalize the case name for comparison
    normalized_case = re.sub(r"[^A-Za-z0-9 ]+", "_", case_name).lower().strip()
    normalized_case_spaces = re.sub(r"[^A-Za-z0-9 ]+", " ", case_name).lower().strip()
    tokens = [t.lower() for t in normalized_case_spaces.split() if len(t) > 2]
    
    # Need at least some tokens to match
    if not tokens:
        return {"query": case_name, "year": year, "matches": [], "count": 0}
    
    matches = []
    # Determine search scope
    if year and (PDF_ROOT / str(year)).exists():
        search_dirs = [PDF_ROOT / str(year)]
    else:
        search_dirs = [d for d in PDF_ROOT.iterdir() if d.is_dir() and d.name.isdigit()]
    
    for d in search_dirs:
        for fname in d.iterdir():
            if not fname.name.lower().endswith('.pdf'):
                continue
            
            # Get filename without extension
            file_base = fname.stem.lower()
            
            # Normalize filename the same way as case name
            normalized_file = re.sub(r"[^a-z0-9 ]+", "_", file_base).strip()
            normalized_file_spaces = re.sub(r"[^a-z0-9 ]+", " ", file_base).strip()
            
            # Priority 1: Exact match (after normalization)
            if normalized_case == normalized_file or normalized_case_spaces == normalized_file_spaces:
                rel_path = f"{d.name}/{fname.name}"
                matches.insert(0, {  # Insert at beginning for exact matches
                    "path": rel_path, 
                    "score": 1000,  # High score for exact match
                    "match_type": "exact"
                })
                continue
            
            # Priority 2: Case name is substring of filename or vice versa
            if normalized_case in normalized_file or normalized_file in normalized_case:
                score = 500 + len(normalized_case)  # Longer matches score higher
                rel_path = f"{d.name}/{fname.name}"
                matches.append({
                    "path": rel_path, 
                    "score": score,
                    "match_type": "substring"
                })
                continue
            
            # Priority 3: All important tokens match in order
            all_tokens_match = all(t in normalized_file_spaces for t in tokens if len(t) > 3)
            if all_tokens_match and len(tokens) >= 3:
                score = 100 + sum(1 for t in tokens if t in normalized_file_spaces)
                rel_path = f"{d.name}/{fname.name}"
                matches.append({
                    "path": rel_path, 
                    "score": score,
                    "match_type": "all_tokens"
                })
    
    # Sort by score (highest first), then by shortest path
    matches.sort(key=lambda m: (-m['score'], len(m['path'])))
    
    # Return only the best match
    top_matches = matches[:1] if matches else []
    
    return {
        "query": case_name, 
        "year": year, 
        "matches": top_matches, 
        "count": len(top_matches)
    }

@app.get("/pdf/file")
def pdf_file(path: str = Query(..., description="Relative path year/filename.PDF under pdf root")):
    target = PDF_ROOT / path
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(str(target), media_type="application/pdf")

@app.get("/pdf/link")
def pdf_link(case_name: str = Query(..., description="Case name to resolve to a single PDF filename"),
             year: int | None = Query(None, description="Optional year restriction")):
    """Return the single best PDF match (simple token scoring) or 404 if none suitable."""
    if not PDF_ROOT.exists():
        raise HTTPException(status_code=404, detail="PDF repository not available")
    normalized = re.sub(r"[^A-Za-z0-9 ]+", " ", case_name)
    tokens = [t.lower() for t in normalized.split() if len(t) > 2]
    if not tokens:
        raise HTTPException(status_code=400, detail="Insufficient tokens to match")
    search_dirs = []
    if year and (PDF_ROOT / str(year)).exists():
        search_dirs.append(PDF_ROOT / str(year))
    else:
        search_dirs.extend([d for d in PDF_ROOT.iterdir() if d.is_dir() and d.name.isdigit()])
    best = None
    for d in search_dirs:
        for fname in d.iterdir():
            if not fname.name.lower().endswith('.pdf'):
                continue
            lower_name = fname.name.lower()
            score = sum(1 for t in tokens if t in lower_name)
            if score == 0:
                continue
            density = score / max(len(tokens), 1)
            candidate = {"path": f"{d.name}/{fname.name}", "score": score, "density": round(density,2)}
            if (best is None) or (candidate['score'] > best['score']) or (candidate['score'] == best['score'] and candidate['density'] > best['density']):
                best = candidate
    if not best:
        raise HTTPException(status_code=404, detail="No matching PDF found")
    best['url'] = f"/pdfs/{best['path']}"
    return best

@app.get("/explain/{doc_id}")
def explain(doc_id: str,
            q: str = Query(..., description="Query to explain"),
            title_boost: float = Query(3.0, ge=1.0, le=10.0),
            search_priority: str = Query("balanced"),
            mode: str = Query("bm25"),
            semantic_weight: float = Query(0.3, ge=0.0, le=1.0),
            es: Elasticsearch = Depends(get_es_client),
            settings: Settings = Depends(get_settings)):
    """Explain score for a single document given the query parameters."""
    try:
        # Build minimal query (no pagination/highlights) for explanation
        query_body = None
        if mode in ["hybrid","semantic"]:
            from .semantic import embed_query, is_available
            if is_available():
                vector = embed_query(q)
                query_body = search.build_hybrid_query(q, vector, title_boost=title_boost, include_highlights=False,
                                                       size=1, from_offset=0, semantic_weight=(1.0 if mode=='semantic' else semantic_weight),
                                                       search_priority=search_priority)
            else:
                mode = "bm25"  # fallback
        if query_body is None:
            query_body = search.build_multi_match_query(q, title_boost=title_boost, include_highlights=False,
                                                        size=1, from_offset=0, search_priority=search_priority)
        try:
            explanation = es.explain(index=settings.index_name, id=doc_id, body={"query": query_body["query"]})
        except Exception as ee:
            msg = str(ee)
            if "[404]" in msg or "NotFound" in msg or "not_found" in msg:
                raise HTTPException(status_code=404, detail=f"Document not found for explain (id={doc_id})")
            raise HTTPException(status_code=500, detail=f"Explain internal error: {msg}")
        if not explanation or not explanation.get('matched', False):
            return {"doc_id": doc_id, "query": q, "mode": mode, "matched": False, "note": "Query did not match document", "query_preview": query_body["query"]}
        return {"doc_id": doc_id, "query": q, "mode": mode, "matched": True, "explanation": explanation, "query_preview": query_body["query"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explain failed: {e}")

@app.get("/live/supreme")
async def live_supreme(
    q: str = Query(..., description="Query string for Supreme Court live search"),
    limit: int = Query(5, ge=1, le=20),
    year: Optional[int] = Query(None, description="Optional year filter (best-effort)"),
):
    """Live (federated) search against eCourts portal for Supreme Court judgments.
    This does NOT use the local index. Results are scraped in real-time and may be
    incomplete or brittle if the upstream DOM changes.
    """
    try:
        data = await live_supreme_search(q, limit=limit, year=year)
        if data.get("error"):
            raise HTTPException(status_code=502, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger_adapter.error("Live eCourts search failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Live search error: {e}")

# Simple cached status for upstream live source
_live_status_cache = {"ts": 0, "data": None}

@app.get("/live/status")
async def live_status():
    """Check availability of external live search provider (Indian Kanoon).
    Returns cached result for 30 seconds to avoid hammering upstream.
    """
    now = time.time()
    if _live_status_cache["data"] and (now - _live_status_cache["ts"] < 30):
        return _live_status_cache["data"]
    url = "https://indiankanoon.org/search/?formInput=doctypes:supremecourt&pagenum=0"
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent":"Mozilla/5.0 LegitSearch"}) as client:
            resp = await client.get(url)
        data = {
            "upstream_url": url,
            "http_status": resp.status_code,
            "ok": resp.status_code < 500,
            "checked_at": int(now),
            "note": "Indian Kanoon sometimes returns intermittent 500 via Cloudflare. Retry later or rely on local index."
        }
        _live_status_cache["ts"], _live_status_cache["data"] = now, data
        return data
    except Exception as e:
        data = {
            "upstream_url": url,
            "http_status": None,
            "ok": False,
            "error": str(e),
            "checked_at": int(now)
        }
        _live_status_cache["ts"], _live_status_cache["data"] = now, data
        return data