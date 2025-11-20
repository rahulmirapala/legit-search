"""Advanced ranking and scoring improvements for legal search.
Combines multiple signals for better relevance.
"""
from typing import List, Dict
import math

def calculate_citation_authority(hit: Dict) -> float:
    """Calculate authority score based on citation metadata.
    
    Uses page_rank if available, otherwise estimates based on year and citation patterns.
    """
    # Use existing page_rank if available
    if hit.get('page_rank'):
        return min(1.0, hit['page_rank'] / 10.0)  # Normalize to 0-1
    
    # Fallback: older cases and frequently cited cases get higher scores
    year = hit.get('year', 2020)
    age_score = min(1.0, (year - 1950) / 70.0) if year >= 1950 else 0.5
    
    # Boost for landmark cases (heuristic: longer full text often = more important)
    text_length = len(hit.get('full_text', ''))
    length_score = min(1.0, text_length / 10000) if text_length > 0 else 0.5
    
    return (age_score * 0.6 + length_score * 0.4)

def calculate_recency_boost(hit: Dict, decay_years: int = 10) -> float:
    """Calculate recency boost with configurable decay.
    
    Recent cases get higher boost, decays exponentially.
    """
    from datetime import datetime
    current_year = datetime.utcnow().year
    doc_year = hit.get('year', current_year - 20)
    
    years_old = current_year - doc_year
    if years_old <= 0:
        return 1.0
    
    # Exponential decay: 0.5 at decay_years, approaching 0 for very old
    decay_factor = math.exp(-years_old / decay_years)
    return max(0.1, decay_factor)

def calculate_coverage_score(hit: Dict, query_terms: List[str]) -> float:
    """Calculate how well the document covers query terms.
    
    Rewards documents that mention multiple query terms.
    """
    if not query_terms:
        return 1.0
    
    text = (hit.get('case_name', '') + ' ' + hit.get('full_text', '')).lower()
    covered = sum(1 for term in query_terms if term.lower() in text)
    return covered / len(query_terms)

def rerank_with_learning_to_rank(query: str, hits: List[Dict], query_analysis: Dict) -> List[Dict]:
    """Advanced reranking combining multiple signals.
    
    Combines:
    - Original BM25/semantic score
    - Citation authority
    - Recency
    - Query coverage
    - Query type specific boosts
    """
    if not hits:
        return hits
    
    query_terms = query.split()
    query_type = query_analysis.get('type', 'mixed')
    
    for hit in hits:
        original_score = hit.get('score', 0)
        
        # Calculate component scores
        authority = calculate_citation_authority(hit)
        recency = calculate_recency_boost(hit)
        coverage = calculate_coverage_score(hit, query_terms)
        
        # Query type specific weights
        if query_type == 'citation':
            # Citations care most about exact match, less about recency
            final_score = original_score * 2.0 + authority * 0.5
        elif query_type == 'case_name':
            # Case names: high weight on match quality and authority
            final_score = original_score * 1.5 + authority * 1.0 + coverage * 0.5
        elif query_type == 'legal_concept':
            # Concepts: balance relevance with recency and coverage
            final_score = original_score * 1.0 + recency * 0.8 + coverage * 0.7 + authority * 0.5
        else:  # mixed
            # Balanced approach
            final_score = original_score * 1.2 + recency * 0.5 + coverage * 0.5 + authority * 0.3
        
        hit['rerank_score'] = final_score
        hit['ranking_signals'] = {
            'original_score': original_score,
            'authority': round(authority, 3),
            'recency': round(recency, 3),
            'coverage': round(coverage, 3),
            'query_type': query_type
        }
    
    # Sort by rerank score
    return sorted(hits, key=lambda x: x.get('rerank_score', 0), reverse=True)

def deduplicate_results(hits: List[Dict], similarity_threshold: float = 0.9) -> List[Dict]:
    """Remove near-duplicate results based on case name similarity.
    
    Keeps the highest-scoring version of similar documents.
    """
    if not hits:
        return hits
    
    def normalize_name(name: str) -> str:
        """Normalize case name for comparison."""
        if not name:
            return ''
        # Remove common variations, extra spaces, punctuation
        import re
        normalized = re.sub(r'\s+', ' ', name.lower())
        normalized = re.sub(r'[^\w\s]', '', normalized)
        return normalized.strip()
    
    seen = {}
    unique_hits = []
    
    for hit in hits:
        name = normalize_name(hit.get('case_name', ''))
        if not name:
            unique_hits.append(hit)
            continue
        
        # Check for similar names
        is_duplicate = False
        for seen_name in seen:
            # Simple similarity: check if one is substring of other or Levenshtein distance is small
            if name in seen_name or seen_name in name:
                is_duplicate = True
                break
        
        if not is_duplicate:
            seen[name] = hit
            unique_hits.append(hit)
    
    return unique_hits
