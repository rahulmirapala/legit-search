#!/usr/bin/env python3
"""Search quality diagnostic tool.

Tests various query types and analyzes search quality issues.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elasticsearch import Elasticsearch
from app.config import Settings
from app.search import build_multi_match_query
import json

# Test queries representing different search patterns
TEST_QUERIES = [
    # Case name searches
    {"query": "Kesavananda Bharati", "type": "case_name", "expected": "Should find Kesavananda Bharati case"},
    {"query": "Maneka Gandhi", "type": "case_name", "expected": "Should find Maneka Gandhi v Union of India"},
    {"query": "Vishaka", "type": "case_name", "expected": "Should find Vishaka guidelines case"},
    
    # Legal concept searches
    {"query": "fundamental rights", "type": "concept", "expected": "Should find cases about fundamental rights"},
    {"query": "natural justice", "type": "concept", "expected": "Should find cases about natural justice"},
    {"query": "habeas corpus", "type": "concept", "expected": "Should find habeas corpus cases"},
    
    # Citation searches
    {"query": "AIR 1973 SC 1461", "type": "citation", "expected": "Should find exact citation"},
    
    # Complex legal concepts
    {"query": "Article 21 right to life", "type": "complex", "expected": "Should find Article 21 cases"},
    {"query": "breach of contract damages", "type": "complex", "expected": "Should find contract breach cases"},
    
    # Short/specific terms
    {"query": "PIL", "type": "acronym", "expected": "Should find Public Interest Litigation cases"},
    {"query": "dowry", "type": "short", "expected": "Should find dowry-related cases"},
]

def analyze_results(query_info, results, total_hits):
    """Analyze search results for quality issues."""
    issues = []
    
    # Check if we got any results
    if total_hits == 0:
        issues.append("❌ NO RESULTS - Zero hits returned")
        return issues
    
    # Check relevance of top results
    top_scores = [r.get('_score', 0) for r in results[:5]]
    if top_scores:
        avg_score = sum(top_scores) / len(top_scores)
        if avg_score < 1.0:
            issues.append(f"⚠️  LOW SCORES - Average top-5 score: {avg_score:.2f}")
    
    # Check for duplicate or near-duplicate results
    case_names = [r.get('_source', {}).get('case_name', '') for r in results[:10]]
    unique_cases = len(set(case_names))
    if unique_cases < len(case_names) * 0.7:
        issues.append(f"⚠️  DUPLICATES - Only {unique_cases} unique cases in top 10")
    
    # Check if query terms appear in top results
    query_terms = set(query_info['query'].lower().split())
    top_result = results[0] if results else None
    if top_result:
        case_name = top_result.get('_source', {}).get('case_name', '').lower()
        full_text = top_result.get('_source', {}).get('full_text', '').lower()[:500]
        
        matched_in_title = sum(1 for term in query_terms if term in case_name)
        matched_in_text = sum(1 for term in query_terms if term in full_text)
        
        if matched_in_title == 0 and matched_in_text == 0:
            issues.append("❌ RELEVANCE - Top result doesn't contain query terms")
    
    if not issues:
        issues.append("✅ OK")
    
    return issues

def run_diagnostics():
    """Run diagnostic tests on search quality."""
    settings = Settings()
    es = Elasticsearch(settings.es_host, request_timeout=30)
    
    if not es.ping():
        print("❌ Cannot connect to Elasticsearch")
        return
    
    print("=" * 80)
    print("SEARCH QUALITY DIAGNOSTIC REPORT")
    print("=" * 80)
    print(f"Index: {settings.index_name}")
    print()
    
    # Get index stats
    try:
        stats = es.count(index=settings.index_name)
        total_docs = stats.get('count', 0)
        print(f"📊 Total documents: {total_docs:,}")
    except Exception as e:
        print(f"⚠️  Could not get document count: {e}")
        total_docs = 0
    
    print()
    print("=" * 80)
    print("TESTING QUERIES")
    print("=" * 80)
    
    results_summary = []
    
    for i, test in enumerate(TEST_QUERIES, 1):
        query = test['query']
        qtype = test['type']
        
        print(f"\n{i}. Query: \"{query}\" (Type: {qtype})")
        print(f"   Expected: {test['expected']}")
        
        try:
            # Build and execute query
            query_body = build_multi_match_query(query, title_boost=3.0, size=10)
            response = es.search(index=settings.index_name, body=query_body)
            
            hits = response.get('hits', {}).get('hits', [])
            total = response.get('hits', {}).get('total', {}).get('value', 0)
            
            print(f"   Results: {total:,} hits")
            
            # Show top 3 results
            if hits:
                print(f"   Top results:")
                for j, hit in enumerate(hits[:3], 1):
                    score = hit.get('_score', 0)
                    case_name = hit.get('_source', {}).get('case_name', 'N/A')
                    year = hit.get('_source', {}).get('year', 'N/A')
                    print(f"      {j}. [{score:.2f}] {case_name} ({year})")
            
            # Analyze issues
            issues = analyze_results(test, hits, total)
            for issue in issues:
                print(f"   {issue}")
            
            results_summary.append({
                'query': query,
                'type': qtype,
                'hits': total,
                'top_score': hits[0].get('_score', 0) if hits else 0,
                'issues': issues
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results_summary.append({
                'query': query,
                'type': qtype,
                'hits': 0,
                'top_score': 0,
                'issues': [f"ERROR: {e}"]
            })
    
    # Summary report
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_tests = len(results_summary)
    zero_results = sum(1 for r in results_summary if r['hits'] == 0)
    low_scores = sum(1 for r in results_summary if r['top_score'] < 1.0 and r['hits'] > 0)
    good_results = sum(1 for r in results_summary if '✅' in str(r['issues']))
    
    print(f"Total queries tested: {total_tests}")
    print(f"Zero results: {zero_results} ({zero_results/total_tests*100:.1f}%)")
    print(f"Low relevance scores: {low_scores} ({low_scores/total_tests*100:.1f}%)")
    print(f"Good results: {good_results} ({good_results/total_tests*100:.1f}%)")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if zero_results > total_tests * 0.2:
        print("🔧 HIGH PRIORITY: Many queries return zero results")
        print("   → Consider: Adding fuzzy matching, expanding synonyms, reducing stopwords")
    
    if low_scores > total_tests * 0.3:
        print("🔧 MEDIUM PRIORITY: Low relevance scores")
        print("   → Consider: Adjusting field boosts, improving BM25 parameters")
    
    if zero_results == 0 and low_scores == 0:
        print("✅ Search quality looks good! Consider fine-tuning for edge cases.")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_diagnostics()
