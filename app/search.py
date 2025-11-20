import nltk
from autocorrect import Speller  # Import Speller
from elasticsearch import Elasticsearch
from datetime import datetime

# --- NLTK setup ---
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# --- Autocorrect Function (Updated) ---
speller = Speller(lang='en')  # Initialize the Speller once

def autospell(text):
    """Corrects spelling of words in a query."""
    spells = [speller(w) for w in (nltk.word_tokenize(text))] # Use speller()
    return " ".join(spells)

# --- Elasticsearch Query Builder (With Dynamic Boost) ---
def build_search_query(query_text: str, title_boost: float = 3.0):
    """Legacy query builder using query_string (kept for reference)."""
    case_name_field = f"case_name^{title_boost}"
    return {
        "query": {
            "query_string": {
                "query": query_text,
                "fields": ["full_text", case_name_field],
                "default_operator": "OR"
            }
        },
        "highlight": {
            "fields": {
                "full_text": {"fragment_size": 150, "number_of_fragments": 3}
            }
        },
        "size": 10
    }

def build_multi_match_query(query_text: str, title_boost: float = 3.0, include_highlights: bool = True,
                            size: int = 10, from_offset: int = 0, filters: dict = None, search_priority: str = "balanced",
                            highlight_size: int = 150, highlight_fragments: int = 3, fuzzy: bool = False):
    """Preferred multi_match query builder with pagination, optional highlights, section-based priority, and optional fuzziness."""
    
    # IMPROVED: Much stronger case_name boosting for better relevance
    # Define field boosts based on search priority
    if search_priority == "heading":
        fields = [
            f"case_name^{title_boost * 6}",  # Increased from 2x to 6x
            f"case_name.shingle^{title_boost * 3}",  # Increased from 1.2x to 3x
            f"case_name.ngram^{title_boost * 1.5}",  # Increased from 0.6x to 1.5x
            "full_text^0.5",  # Reduced from 1.0 to 0.5
            "full_text.shingle^0.3"  # Reduced from 0.6 to 0.3
        ]
    elif search_priority == "introduction":
        fields = [
            f"case_name^{title_boost * 4}",  # Increased significantly
            f"case_name.shingle^{title_boost * 2}",
            f"case_name.ngram^{title_boost}",
            "full_text^1.0",
            "full_text.shingle^0.5"
        ]
    elif search_priority == "body":
        fields = [
            f"case_name^{title_boost * 2}",  # Still boost case_name even in body mode
            "case_name.shingle",
            "case_name.ngram^0.5",
            "full_text^2",
            "full_text.shingle^0.8"
        ]
    elif search_priority == "conclusion":
        fields = [
            f"case_name^{title_boost}",
            "case_name.shingle^0.5",
            "case_name.ngram^0.3",
            "full_text^1.8",
            "full_text.shingle^0.7"
        ]
    else:  # balanced - MOST IMPORTANT FOR DEFAULT SEARCHES
        fields = [
            f"case_name^{title_boost * 5}",  # Increased from 1x to 5x (default 15.0 boost)
            f"case_name.shingle^{title_boost * 2.5}",  # Increased from 0.7x to 2.5x
            f"case_name.ngram^{title_boost * 1.2}",  # Increased from 0.5x to 1.2x
            "full_text^0.8",  # Reduced from 1.0 to 0.8
            "full_text.shingle^0.4"  # Reduced from 0.6 to 0.4
        ]
    
    # Build the query with improved matching strategy
    mm = {
        "query": query_text,
        "fields": fields,
        "type": "cross_fields",  # Changed from best_fields to cross_fields for better coordination
        "tie_breaker": 0.3,  # Increased from 0.2 to 0.3
        "operator": "or",  # Use OR but add minimum_should_match below
        "minimum_should_match": "2<75%"  # If 2 terms: 100% match, 3+ terms: 75% match
    }
    if fuzzy:
        mm["fuzziness"] = "AUTO"
        mm["prefix_length"] = 2
        mm["operator"] = "OR"
    query_clause = {"multi_match": mm}
    
    # Add filters if provided
    if filters:
        filter_clauses = []
        if filters.get('year_from') or filters.get('year_to'):
            year_filter = {"range": {"year": {}}}
            if filters.get('year_from'):
                year_filter["range"]["year"]["gte"] = filters['year_from']
            if filters.get('year_to'):
                year_filter["range"]["year"]["lte"] = filters['year_to']
            filter_clauses.append(year_filter)
        
        if filters.get('court'):
            filter_clauses.append({"term": {"court": filters['court']}})
        
        if filter_clauses:
            query_clause = {
                "bool": {
                    "must": query_clause,
                    "filter": filter_clauses
                }
            }
    
    # Wrap with function_score for recency and authority boosts
    current_year = datetime.utcnow().year
    body = {
        "from": from_offset,
        "size": size,
        "query": {
            "function_score": {
                "query": query_clause,
                "score_mode": "sum",
                "boost_mode": "sum",
                "functions": [
                    {"field_value_factor": {"field": "page_rank", "missing": 1.0, "modifier": "log1p"}, "weight": 0.2},
                    {"exp": {"year": {"origin": current_year, "scale": 10, "decay": 0.5}}, "weight": 0.3}
                ]
            }
        }
    }
    
    if include_highlights:
        body["highlight"] = {
            "fields": {
                "full_text": {
                    "fragment_size": highlight_size,
                    "number_of_fragments": highlight_fragments
                }
            }
        }
    return body

def build_hybrid_query(query_text: str, query_vector, title_boost: float = 3.0, 
                      include_highlights: bool = True, size: int = 10, 
                      from_offset: int = 0, semantic_weight: float = 0.3, filters: dict = None, search_priority: str = "balanced",
                      highlight_size: int = 150, highlight_fragments: int = 3):
    """Hybrid search combining BM25 and semantic vector search with section-based priority.
    
    Args:
        query_text: Text query for BM25
        query_vector: Embedding vector for semantic search
        semantic_weight: Weight for semantic score (0.0-1.0), BM25 gets (1-weight)
        filters: Optional dict with year_from, year_to, court filters
        search_priority: Section priority (heading, introduction, body, conclusion, balanced)
    """
    bm25_weight = 1.0 - semantic_weight
    
    # IMPROVED: Match the better field boosting from build_multi_match_query
    if search_priority == "heading":
        fields = [
            f"case_name^{title_boost * 6}",
            f"case_name.shingle^{title_boost * 3}",
            f"case_name.ngram^{title_boost * 1.5}",
            "full_text^0.5",
            "full_text.shingle^0.3"
        ]
    elif search_priority == "introduction":
        fields = [
            f"case_name^{title_boost * 4}",
            f"case_name.shingle^{title_boost * 2}",
            f"case_name.ngram^{title_boost}",
            "full_text^1.0",
            "full_text.shingle^0.5"
        ]
    elif search_priority == "body":
        fields = [
            f"case_name^{title_boost * 2}",
            "case_name.shingle",
            "case_name.ngram^0.5",
            "full_text^2",
            "full_text.shingle^0.8"
        ]
    elif search_priority == "conclusion":
        fields = [
            f"case_name^{title_boost}",
            "case_name.shingle^0.5",
            "case_name.ngram^0.3",
            "full_text^1.8",
            "full_text.shingle^0.7"
        ]
    else:  # balanced
        fields = [
            f"case_name^{title_boost * 5}",
            f"case_name.shingle^{title_boost * 2.5}",
            f"case_name.ngram^{title_boost * 1.2}",
            "full_text^0.8",
            "full_text.shingle^0.4"
        ]
    
    # Build filter clauses
    filter_clauses = []
    if filters:
        if filters.get('year_from') or filters.get('year_to'):
            year_filter = {"range": {"year": {}}}
            if filters.get('year_from'):
                year_filter["range"]["year"]["gte"] = filters['year_from']
            if filters.get('year_to'):
                year_filter["range"]["year"]["lte"] = filters['year_to']
            filter_clauses.append(year_filter)
        
        if filters.get('court'):
            filter_clauses.append({"term": {"court": filters['court']}})
    
    # Safe semantic script: guard missing embedding field to avoid runtime errors.
    semantic_script = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "doc['embedding'].size()==0 ? 0.0 : cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                "params": {"query_vector": query_vector}
            },
            "boost": semantic_weight
        }
    }

    current_year = datetime.utcnow().year
    body = {
        "from": from_offset,
        "size": size,
        "query": {
            "function_score": {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": query_text,
                                    "fields": fields,
                                    "type": "cross_fields",
                                    "tie_breaker": 0.3,
                                    "operator": "or",
                                    "minimum_should_match": "2<75%",
                                    "boost": bm25_weight
                                }
                            },
                            semantic_script
                        ],
                        "filter": []
                    }
                },
                "score_mode": "sum",
                "boost_mode": "sum",
                "functions": [
                    {"field_value_factor": {"field": "page_rank", "missing": 1.0, "modifier": "log1p"}, "weight": 0.2},
                    {"exp": {"year": {"origin": current_year, "scale": 10, "decay": 0.5}}, "weight": 0.3}
                ]
            }
        }
    }
    
    # Merge user filters with embedding existence filter if both present
    if filter_clauses:
        # Insert filters into the inner bool
        inner_bool = body["query"]["function_score"]["query"]["bool"]
        existing_filters = inner_bool.get("filter", [])
        inner_bool["filter"] = existing_filters + filter_clauses
    
    if include_highlights:
        body["highlight"] = {
            "fields": {
                "full_text": {
                    "fragment_size": highlight_size,
                    "number_of_fragments": highlight_fragments
                }
            }
        }
    return body