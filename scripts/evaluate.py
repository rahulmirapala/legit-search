"""Evaluation harness for comparing retrieval quality across different modes.

This script allows you to evaluate and compare:
- BM25 baseline
- BM25 + spell correction
- BM25 + LLM expansion
- Hybrid (BM25 + semantic)
- Semantic only
- With/without reranking

Usage:
    python scripts/evaluate.py --queries queries.jsonl --qrels qrels.jsonl
"""

import argparse
import json
import requests
import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict

class Evaluator:
    """Evaluation metrics calculator."""
    
    @staticmethod
    def precision_at_k(retrieved: List[str], relevant: set, k: int = 10) -> float:
        """Calculate Precision@K."""
        retrieved_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc_id in retrieved_k if doc_id in relevant)
        return relevant_retrieved / k if k > 0 else 0.0
    
    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: set, k: int = 10) -> float:
        """Calculate Recall@K."""
        retrieved_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc_id in retrieved_k if doc_id in relevant)
        return relevant_retrieved / len(relevant) if len(relevant) > 0 else 0.0
    
    @staticmethod
    def mean_reciprocal_rank(retrieved: List[str], relevant: set) -> float:
        """Calculate Mean Reciprocal Rank."""
        for i, doc_id in enumerate(retrieved, 1):
            if doc_id in relevant:
                return 1.0 / i
        return 0.0
    
    @staticmethod
    def ndcg_at_k(retrieved: List[str], relevance: Dict[str, int], k: int = 10) -> float:
        """Calculate Normalized Discounted Cumulative Gain@K."""
        retrieved_k = retrieved[:k]
        
        # DCG
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_k, 1):
            rel = relevance.get(doc_id, 0)
            dcg += (2 ** rel - 1) / np.log2(i + 1)
        
        # IDCG
        ideal_rels = sorted(relevance.values(), reverse=True)[:k]
        idcg = sum((2 ** rel - 1) / np.log2(i + 1) for i, rel in enumerate(ideal_rels, 1))
        
        return dcg / idcg if idcg > 0 else 0.0

def load_queries(filepath: str) -> List[Dict]:
    """Load queries from JSONL file.
    
    Format: {"query_id": "Q1", "text": "fundamental rights"}
    """
    queries = []
    with open(filepath, 'r') as f:
        for line in f:
            queries.append(json.loads(line))
    return queries

def load_qrels(filepath: str) -> Dict[str, Dict[str, int]]:
    """Load relevance judgments from JSONL file.
    
    Format: {"query_id": "Q1", "doc_id": "doc123", "relevance": 2}
    Returns: {query_id: {doc_id: relevance}}
    """
    qrels = defaultdict(dict)
    with open(filepath, 'r') as f:
        for line in f:
            entry = json.loads(line)
            qrels[entry['query_id']][entry['doc_id']] = entry['relevance']
    return qrels

def search_api(query: str, mode: str = "bm25", expand: bool = False, 
               spell: bool = True, rerank: bool = False, 
               api_url: str = "http://localhost:8000") -> List[str]:
    """Call the search API and return list of document IDs."""
    params = {
        "q": query,
        "mode": mode,
        "expand": expand,
        "spell": spell,
        "rerank": rerank,
        "page_size": 100
    }
    
    response = requests.get(f"{api_url}/search", params=params)
    response.raise_for_status()
    
    results = response.json()['results']
    # Assuming results have 'id' or 'citation_id' field
    return [r.get('citation_id', r.get('id', '')) for r in results]

def evaluate_configuration(queries: List[Dict], qrels: Dict, config: Dict, 
                          api_url: str = "http://localhost:8000") -> Dict:
    """Evaluate a specific configuration across all queries."""
    metrics = {
        'p@5': [],
        'p@10': [],
        'r@10': [],
        'mrr': [],
        'ndcg@10': []
    }
    
    evaluator = Evaluator()
    
    for query in queries:
        query_id = query['query_id']
        query_text = query['text']
        
        if query_id not in qrels:
            continue
        
        # Get search results
        try:
            retrieved = search_api(
                query_text,
                mode=config.get('mode', 'bm25'),
                expand=config.get('expand', False),
                spell=config.get('spell', True),
                rerank=config.get('rerank', False),
                api_url=api_url
            )
        except Exception as e:
            print(f"Error searching for query {query_id}: {e}")
            continue
        
        # Calculate metrics
        relevant_docs = set(qrels[query_id].keys())
        relevance_scores = qrels[query_id]
        
        metrics['p@5'].append(evaluator.precision_at_k(retrieved, relevant_docs, k=5))
        metrics['p@10'].append(evaluator.precision_at_k(retrieved, relevant_docs, k=10))
        metrics['r@10'].append(evaluator.recall_at_k(retrieved, relevant_docs, k=10))
        metrics['mrr'].append(evaluator.mean_reciprocal_rank(retrieved, relevant_docs))
        metrics['ndcg@10'].append(evaluator.ndcg_at_k(retrieved, relevance_scores, k=10))
    
    # Compute averages
    return {
        metric: np.mean(values) if values else 0.0
        for metric, values in metrics.items()
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality")
    parser.add_argument('--queries', required=True, help="Path to queries JSONL file")
    parser.add_argument('--qrels', required=True, help="Path to qrels JSONL file")
    parser.add_argument('--api-url', default="http://localhost:8000", help="API base URL")
    parser.add_argument('--output', default="evaluation_results.json", help="Output file")
    
    args = parser.parse_args()
    
    # Load data
    print("Loading queries and relevance judgments...")
    queries = load_queries(args.queries)
    qrels = load_qrels(args.qrels)
    print(f"Loaded {len(queries)} queries and {len(qrels)} query-doc mappings")
    
    # Define configurations to test
    configurations = [
        {"name": "BM25 Baseline", "mode": "bm25", "expand": False, "spell": False, "rerank": False},
        {"name": "BM25 + Spell", "mode": "bm25", "expand": False, "spell": True, "rerank": False},
        {"name": "BM25 + Expand", "mode": "bm25", "expand": True, "spell": True, "rerank": False},
        {"name": "Hybrid", "mode": "hybrid", "expand": False, "spell": True, "rerank": False},
        {"name": "Semantic", "mode": "semantic", "expand": False, "spell": False, "rerank": False},
        {"name": "BM25 + Rerank", "mode": "bm25", "expand": False, "spell": True, "rerank": True},
        {"name": "Hybrid + Rerank", "mode": "hybrid", "expand": True, "spell": True, "rerank": True},
    ]
    
    # Evaluate each configuration
    results = {}
    for config in configurations:
        print(f"\nEvaluating: {config['name']}")
        metrics = evaluate_configuration(queries, qrels, config, args.api_url)
        results[config['name']] = metrics
        
        # Print results
        print(f"  P@5:      {metrics['p@5']:.4f}")
        print(f"  P@10:     {metrics['p@10']:.4f}")
        print(f"  R@10:     {metrics['r@10']:.4f}")
        print(f"  MRR:      {metrics['mrr']:.4f}")
        print(f"  NDCG@10:  {metrics['ndcg@10']:.4f}")
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to {args.output}")
    
    # Print comparison table
    print("\n" + "="*80)
    print("COMPARISON TABLE")
    print("="*80)
    print(f"{'Configuration':<25} {'P@5':>8} {'P@10':>8} {'R@10':>8} {'MRR':>8} {'NDCG@10':>10}")
    print("-"*80)
    for name, metrics in results.items():
        print(f"{name:<25} {metrics['p@5']:>8.4f} {metrics['p@10']:>8.4f} "
              f"{metrics['r@10']:>8.4f} {metrics['mrr']:>8.4f} {metrics['ndcg@10']:>10.4f}")

if __name__ == "__main__":
    main()
