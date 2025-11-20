"""
Advanced autocomplete and spell suggestion system for legal search.

Features:
- Multi-field completion (case names, legal terms, citations)
- Fuzzy matching for typos
- Phrase suggestions
- Query history learning
- Legal domain-specific suggestions
"""

from elasticsearch import Elasticsearch
import re
from typing import List, Dict, Any, Optional
import Levenshtein  # For edit distance
from collections import Counter


# Legal domain keywords that should get priority in suggestions
LEGAL_KEYWORDS = {
    # Constitutional terms
    "article", "amendment", "constitution", "fundamental", "rights", "directive",
    "schedule", "preamble", "writs", "habeas", "mandamus", "certiorari", "quo warranto",
    
    # Case types
    "civil", "criminal", "writ", "petition", "appeal", "revision", "reference",
    "special leave", "slp", "pil", "suo motu",
    
    # Legal concepts
    "jurisdiction", "precedent", "ratio decidendi", "obiter dicta", "stare decisis",
    "natural justice", "audi alteram partem", "nemo judex", "res judicata",
    "ultra vires", "locus standi", "bona fide", "mala fide", "prima facie",
    
    # IPC sections (common ones)
    "section 302", "section 307", "section 420", "section 498a", "section 376",
    "section 304", "section 120b", "section 34",
    
    # Court terminology
    "plaintiff", "defendant", "petitioner", "respondent", "appellant", "bench",
    "judgment", "order", "decree", "injunction", "bail", "custody", "evidence",
    "testimony", "witness", "cross-examination", "summons", "warrant"
}


def normalize_text(text: str) -> str:
    """Normalize text for matching."""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\-]', '', text)
    return text


def calculate_relevance_score(suggestion: str, prefix: str, doc_count: int = 1) -> float:
    """
    Calculate relevance score for a suggestion.
    
    Factors:
    - Edit distance from prefix
    - Length similarity
    - Document frequency
    - Legal keyword presence
    """
    norm_sugg = normalize_text(suggestion)
    norm_prefix = normalize_text(prefix)
    
    # Base score from document frequency (log scale)
    import math
    freq_score = math.log(doc_count + 1)
    
    # Position bonus (earlier match is better)
    if norm_sugg.startswith(norm_prefix):
        position_score = 10.0
    else:
        position_score = 5.0 / (norm_sugg.find(norm_prefix) + 1) if norm_prefix in norm_sugg else 0
    
    # Edit distance penalty
    edit_dist = Levenshtein.distance(norm_prefix, norm_sugg[:len(norm_prefix)])
    edit_score = 5.0 / (edit_dist + 1)
    
    # Legal keyword bonus
    legal_bonus = 0
    for keyword in LEGAL_KEYWORDS:
        if keyword in norm_sugg:
            legal_bonus += 2.0
    
    # Length similarity bonus (prefer similar length)
    len_diff = abs(len(norm_sugg) - len(norm_prefix))
    len_score = 5.0 / (len_diff + 1) if len_diff < 20 else 0
    
    total_score = freq_score + position_score + edit_score + legal_bonus + len_score
    return round(total_score, 2)


class AutocompleteEngine:
    """Advanced autocomplete engine for legal search."""
    
    def __init__(self, es_client: Elasticsearch, index_name: str):
        self.es = es_client
        self.index_name = index_name
    
    def get_case_name_suggestions(self, prefix: str, limit: int = 10, fuzzy: bool = True) -> List[Dict[str, Any]]:
        """Get case name suggestions with fuzzy matching."""
        if len(prefix) < 2:
            return []
        
        # Build query with fuzzy matching
        query = {
            "size": 0,
            "aggs": {
                "case_names": {
                    "terms": {
                        "field": "case_name.keyword",
                        "size": limit * 3,  # Get more to filter/rank
                        "order": {"_count": "desc"}
                    }
                }
            }
        }
        
        # Add filter for case names starting with prefix
        norm_prefix = normalize_text(prefix)
        
        if fuzzy:
            # Use match query with fuzziness
            query["query"] = {
                "match": {
                    "case_name": {
                        "query": prefix,
                        "fuzziness": "AUTO",
                        "prefix_length": 2
                    }
                }
            }
        else:
            # Exact prefix match
            query["query"] = {
                "match_phrase_prefix": {
                    "case_name": prefix
                }
            }
        
        try:
            resp = self.es.search(index=self.index_name, body=query)
            buckets = resp.get('aggregations', {}).get('case_names', {}).get('buckets', [])
            
            suggestions = []
            for bucket in buckets:
                case_name = bucket['key']
                doc_count = bucket['doc_count']
                
                # Filter: must contain prefix (case-insensitive)
                if norm_prefix not in normalize_text(case_name):
                    continue
                
                score = calculate_relevance_score(case_name, prefix, doc_count)
                suggestions.append({
                    "text": case_name,
                    "type": "case_name",
                    "frequency": doc_count,
                    "score": score
                })
            
            # Sort by score and limit
            suggestions.sort(key=lambda x: x['score'], reverse=True)
            return suggestions[:limit]
        
        except Exception as e:
            print(f"Case name suggestion error: {e}")
            return []
    
    def get_legal_term_suggestions(self, prefix: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get legal term suggestions from predefined keywords."""
        norm_prefix = normalize_text(prefix)
        
        suggestions = []
        for keyword in LEGAL_KEYWORDS:
            if norm_prefix in normalize_text(keyword):
                score = calculate_relevance_score(keyword, prefix)
                suggestions.append({
                    "text": keyword.title(),
                    "type": "legal_term",
                    "frequency": 0,
                    "score": score
                })
        
        # Sort by score and limit
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions[:limit]
    
    def get_citation_suggestions(self, prefix: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get citation suggestions (e.g., '2020 SCR', 'AIR 1973')."""
        if len(prefix) < 2:
            return []
        
        # Look for citations in citation_id field
        query = {
            "size": 0,
            "query": {
                "match_phrase_prefix": {
                    "citation_id": prefix
                }
            },
            "aggs": {
                "citations": {
                    "terms": {
                        "field": "citation_id.keyword",
                        "size": limit,
                        "order": {"_count": "desc"}
                    }
                }
            }
        }
        
        try:
            resp = self.es.search(index=self.index_name, body=query)
            buckets = resp.get('aggregations', {}).get('citations', {}).get('buckets', [])
            
            suggestions = []
            for bucket in buckets:
                citation = bucket['key']
                doc_count = bucket['doc_count']
                
                if citation and normalize_text(prefix) in normalize_text(citation):
                    score = calculate_relevance_score(citation, prefix, doc_count)
                    suggestions.append({
                        "text": citation,
                        "type": "citation",
                        "frequency": doc_count,
                        "score": score
                    })
            
            suggestions.sort(key=lambda x: x['score'], reverse=True)
            return suggestions[:limit]
        
        except Exception as e:
            print(f"Citation suggestion error: {e}")
            return []
    
    def get_phrase_suggestions(self, text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get multi-word phrase suggestions from full_text field."""
        if len(text) < 3:
            return []
        
        # Use shingles or phrase prefix query on full_text
        query = {
            "size": 0,
            "query": {
                "match_phrase_prefix": {
                    "full_text": {
                        "query": text,
                        "slop": 2
                    }
                }
            },
            "aggs": {
                "phrases": {
                    "significant_text": {
                        "field": "full_text",
                        "size": limit * 2,
                        "filter_duplicate_text": True
                    }
                }
            }
        }
        
        try:
            resp = self.es.search(index=self.index_name, body=query)
            buckets = resp.get('aggregations', {}).get('phrases', {}).get('buckets', [])
            
            suggestions = []
            norm_text = normalize_text(text)
            
            for bucket in buckets:
                phrase = bucket['key']
                doc_count = bucket.get('doc_count', 0)
                
                # Filter: must contain search text
                if norm_text in normalize_text(phrase):
                    score = calculate_relevance_score(phrase, text, doc_count)
                    suggestions.append({
                        "text": phrase,
                        "type": "phrase",
                        "frequency": doc_count,
                        "score": score
                    })
            
            suggestions.sort(key=lambda x: x['score'], reverse=True)
            return suggestions[:limit]
        
        except Exception as e:
            print(f"Phrase suggestion error: {e}")
            return []
    
    def get_all_suggestions(
        self,
        text: str,
        limit: int = 10,
        include_case_names: bool = True,
        include_legal_terms: bool = True,
        include_citations: bool = True,
        include_phrases: bool = True,
        fuzzy: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get comprehensive suggestions from all sources.
        
        Returns merged and ranked suggestions.
        """
        all_suggestions = []
        
        # Get suggestions from different sources
        if include_case_names:
            case_suggestions = self.get_case_name_suggestions(text, limit=limit, fuzzy=fuzzy)
            all_suggestions.extend(case_suggestions)
        
        if include_legal_terms:
            term_suggestions = self.get_legal_term_suggestions(text, limit=5)
            all_suggestions.extend(term_suggestions)
        
        if include_citations:
            citation_suggestions = self.get_citation_suggestions(text, limit=5)
            all_suggestions.extend(citation_suggestions)
        
        if include_phrases and len(text.split()) > 1:
            phrase_suggestions = self.get_phrase_suggestions(text, limit=5)
            all_suggestions.extend(phrase_suggestions)
        
        # Remove duplicates (by text)
        seen = set()
        unique_suggestions = []
        for sugg in all_suggestions:
            if sugg['text'] not in seen:
                seen.add(sugg['text'])
                unique_suggestions.append(sugg)
        
        # Sort by score
        unique_suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return unique_suggestions[:limit]


class SpellChecker:
    """Enhanced spell checker for legal terms."""
    
    def __init__(self, es_client: Elasticsearch, index_name: str):
        self.es = es_client
        self.index_name = index_name
        self.legal_dictionary = LEGAL_KEYWORDS
    
    def suggest_corrections(self, text: str, max_suggestions: int = 5) -> List[Dict[str, Any]]:
        """
        Suggest spelling corrections using Elasticsearch suggest API.
        """
        if len(text) < 3:
            return []
        
        words = text.split()
        all_corrections = []
        
        for word in words:
            if len(word) < 3:
                continue
            
            # Use term suggester for individual words
            suggest_query = {
                "suggest": {
                    f"{word}_suggest": {
                        "text": word,
                        "term": {
                            "field": "case_name",
                            "suggest_mode": "popular",
                            "min_word_length": 3,
                            "prefix_length": 1,
                            "max_edits": 2,
                            "max_term_freq": 0.01
                        }
                    }
                }
            }
            
            try:
                resp = self.es.search(index=self.index_name, body=suggest_query)
                suggestions = resp.get('suggest', {}).get(f"{word}_suggest", [])
                
                for suggestion_group in suggestions:
                    for option in suggestion_group.get('options', [])[:3]:
                        all_corrections.append({
                            "original": word,
                            "correction": option['text'],
                            "score": option.get('score', 0),
                            "frequency": option.get('freq', 0)
                        })
            except Exception as e:
                print(f"Spell check error for '{word}': {e}")
        
        # Sort by score
        all_corrections.sort(key=lambda x: x['score'], reverse=True)
        return all_corrections[:max_suggestions]
    
    def correct_query(self, text: str) -> Optional[str]:
        """
        Return corrected query if spelling errors detected.
        """
        corrections = self.suggest_corrections(text, max_suggestions=10)
        
        if not corrections:
            return None
        
        # Build corrected query
        corrected = text
        for corr in corrections:
            # Replace only if significantly different and high confidence
            if corr['score'] > 0.5 and corr['original'] != corr['correction']:
                corrected = corrected.replace(corr['original'], corr['correction'])
        
        return corrected if corrected != text else None


def get_autocomplete_engine(es_client: Elasticsearch, index_name: str) -> AutocompleteEngine:
    """Factory function to create autocomplete engine."""
    return AutocompleteEngine(es_client, index_name)


def get_spell_checker(es_client: Elasticsearch, index_name: str) -> SpellChecker:
    """Factory function to create spell checker."""
    return SpellChecker(es_client, index_name)
