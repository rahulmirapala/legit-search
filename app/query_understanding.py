"""Query understanding and intelligent routing for legal search.
Analyzes queries to detect intent (case name, citation, concept) and adjusts field weights accordingly.
"""
import re
from typing import Dict, Literal

QueryType = Literal["citation", "case_name", "legal_concept", "mixed"]

# Citation patterns
CITATION_PATTERNS = [
    r'\(\d{4}\)\s*\d+\s+SCC\s+\d+',  # (2017) 10 SCC 1
    r'\d{4}\s+SCC\s+\d+',  # 2017 SCC 10
    r'AIR\s+\d{4}\s+SC\s+\d+',  # AIR 2017 SC 4161
    r'\[\d{4}\]\s+\d+\s+SCR\s+\d+',  # [2017] 1 SCR 1
]

# Legal concept indicators
LEGAL_CONCEPTS = {
    'constitutional': ['article', 'constitution', 'fundamental right', 'directive principle', 'amendment'],
    'criminal': ['section', 'ipc', 'crpc', 'fir', 'cognizable', 'bail', 'conviction', 'sentence'],
    'civil': ['suit', 'damages', 'injunction', 'specific performance', 'decree', 'appeal'],
    'procedural': ['jurisdiction', 'limitation', 'evidence', 'procedure', 'writ', 'habeas corpus', 'mandamus'],
    'family': ['marriage', 'divorce', 'maintenance', 'custody', 'adoption', 'alimony'],
    'property': ['property', 'ownership', 'possession', 'easement', 'transfer', 'lease'],
    'commercial': ['contract', 'partnership', 'company', 'arbitration', 'negotiable instrument', 'insolvency'],
}

def detect_query_type(query: str) -> Dict[str, any]:
    """Analyze query to determine type and confidence.
    
    Returns:
        dict with 'type', 'confidence', 'features', and 'routing_hints'
    """
    q_lower = query.lower().strip()
    q_normalized = re.sub(r'\s+', ' ', q_lower)
    
    # Check for citation patterns
    for pattern in CITATION_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return {
                'type': 'citation',
                'confidence': 0.95,
                'features': {'has_citation': True},
                'routing_hints': {
                    'boost_fields': ['citation_id^10', 'case_name^3'],
                    'use_fuzzy': False,
                    'expand': False
                }
            }
    
    # Check for case name patterns (vs. prefix, proper nouns, capitalized)
    words = query.split()
    capitalized_ratio = sum(1 for w in words if w and w[0].isupper()) / max(len(words), 1)
    has_vs = ' v. ' in query or ' vs. ' in query.lower() or ' v ' in query
    
    if (capitalized_ratio > 0.6 or has_vs) and len(words) >= 2:
        return {
            'type': 'case_name',
            'confidence': 0.85 if has_vs else 0.7,
            'features': {'capitalized_ratio': capitalized_ratio, 'has_vs': has_vs},
            'routing_hints': {
                'boost_fields': ['case_name^8', 'case_name.ngram^4', 'case_name.shingle^3'],
                'use_fuzzy': True,
                'expand': False
            }
        }
    
    # Check for legal concepts
    concept_scores = {}
    for category, terms in LEGAL_CONCEPTS.items():
        score = sum(1 for term in terms if term in q_normalized)
        if score > 0:
            concept_scores[category] = score
    
    if concept_scores:
        top_category = max(concept_scores, key=concept_scores.get)
        return {
            'type': 'legal_concept',
            'confidence': min(0.9, 0.5 + concept_scores[top_category] * 0.1),
            'features': {'concept_category': top_category, 'concept_scores': concept_scores},
            'routing_hints': {
                'boost_fields': ['full_text^2', 'full_text.shingle^1.5', 'case_name^1'],
                'use_fuzzy': False,
                'expand': True,
                'synonyms': True
            }
        }
    
    # Default: mixed/general query
    return {
        'type': 'mixed',
        'confidence': 0.5,
        'features': {},
        'routing_hints': {
            'boost_fields': ['case_name^3', 'full_text'],
            'use_fuzzy': len(q_normalized) > 15,  # Fuzzy for longer queries
            'expand': True
        }
    }

def get_adaptive_fields(query: str, base_title_boost: float = 3.0) -> list[str]:
    """Return field list with adaptive boosts based on query type."""
    analysis = detect_query_type(query)
    hints = analysis['routing_hints']
    
    if 'boost_fields' in hints:
        return hints['boost_fields']
    
    # Fallback
    return [f"case_name^{base_title_boost}", "full_text"]

def should_expand(query: str) -> bool:
    """Determine if query should use expansion based on type."""
    analysis = detect_query_type(query)
    return analysis['routing_hints'].get('expand', True)

def should_use_fuzzy(query: str) -> bool:
    """Determine if fuzzy matching is appropriate."""
    analysis = detect_query_type(query)
    return analysis['routing_hints'].get('use_fuzzy', False)
