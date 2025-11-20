from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class SearchHit(BaseModel):
    score: float | None
    case_name: Optional[str]
    judgment_date: Optional[str]
    citation_id: Optional[str]
    year: Optional[int]
    highlights: List[str]
    pdf_candidates: Optional[List[str]] = None
    pdf_url: Optional[str] = None  # Direct PDF link if deterministically matched

class SearchResponse(BaseModel):
    original_query: str
    corrected_query: str
    expanded_terms: List[str]
    final_query: str
    title_boost_used: float
    page: int
    page_size: int
    total_hits: int
    results: List[SearchHit]
    raw_query: Optional[Dict[str, Any]] = None  # Optional Elasticsearch query body when requested
    llm_rewrite: Optional[str] = None  # Optional refined query suggested by LLM
    classification: Optional[List[str]] = None  # Optional topic labels suggested by LLM
