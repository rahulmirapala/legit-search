"""Query validation and cleaning for legal search.
Prevents useless queries and improves search quality.
"""
import re
from typing import Tuple, Optional

# Common legal stopwords that shouldn't be searched alone
LEGAL_STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
    'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'will',
    'with', 'shall', 'been', 'being', 'were', 'had', 'have', 'or', 'not', 'but',
    'can', 'may', 'such', 'any', 'all', 'no', 'if', 'so', 'which', 'who', 'whom',
    'this', 'these', 'those', 'what', 'when', 'where', 'whether', 'while', 'said'
}

MIN_QUERY_LENGTH = 2  # Minimum characters for a valid search term
MIN_MEANINGFUL_WORDS = 1  # At least one word > 2 chars after stopwords removed

def clean_query(query: str) -> Tuple[str, bool, Optional[str]]:
    """Clean and validate search query.
    
    Returns:
        (cleaned_query, is_valid, error_message)
    """
    if not query or not query.strip():
        return ('', False, 'Query cannot be empty')
    
    original = query.strip()
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', original)
    
    # Check minimum length
    if len(cleaned) < MIN_QUERY_LENGTH:
        return (cleaned, False, f'Query too short. Please enter at least {MIN_QUERY_LENGTH} characters.')
    
    # Tokenize and analyze
    tokens = cleaned.lower().split()
    
    # Single character queries are almost always useless
    if len(tokens) == 1 and len(tokens[0]) == 1:
        return (cleaned, False, 'Single character searches are not supported. Please enter a meaningful search term (case name, citation, or legal concept).')
    
    # Check if query is only stopwords
    meaningful_tokens = [t for t in tokens if t not in LEGAL_STOPWORDS and len(t) > 2]
    
    if not meaningful_tokens:
        return (cleaned, False, 'Please enter a more specific search term. Try a case name, citation, or legal concept.')
    
    # Query is valid
    return (cleaned, True, None)
    meaningful