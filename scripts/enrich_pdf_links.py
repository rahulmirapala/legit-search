#!/usr/bin/env python3
"""Enrich Elasticsearch documents with deterministic PDF filename links.

Dry-run by default unless --commit is supplied.

Quick examples:
    # Preview planned updates (no writes)
    python scripts/enrich_pdf_links.py --index legit_search_index --pdf-root data/supreme_court_judgments --dry-run

    # Commit updates with relaxed density threshold
    python scripts/enrich_pdf_links.py --index legit_search_index --pdf-root data/supreme_court_judgments --min-density 0.3 --commit

Logic:
    1. Load list of PDFs grouped by year (numeric subfolders).
    2. For each ES document missing `pdf_filename`, tokenize its case_name.
    3. Score each PDF filename in the matching year folder (or all years if year missing).
         - Score = token overlap count
         - Density = overlap / token_count(case_name)
    4. Accept best candidate meeting overlap >= min-score and density >= min-density.
    5. Update doc with `pdf_filename`, `pdf_url`, and match diagnostics if committing.

Notes:
    - Heuristic; for production consider fuzzy libraries (rapidfuzz) and authoritative citation ↔ filename mapping.
    - Re-runnable: skips docs already having pdf_filename unless --force.
    - You can lower thresholds to increase recall (risking precision) or raise them to be conservative.
"""
from __future__ import annotations
import argparse, re, sys, math
from pathlib import Path
from typing import Dict, List, Tuple
from elasticsearch import Elasticsearch, helpers

MIN_TOKEN_LEN_DEFAULT = 3
MIN_SCORE_DEFAULT = 2
MIN_DENSITY_DEFAULT = 0.5
BATCH_SIZE_DEFAULT = 500

TOKEN_CLEAN_RE = re.compile(r"[^A-Za-z0-9 ]+")


def tokenize(text: str, min_len: int) -> List[str]:
    text = TOKEN_CLEAN_RE.sub(" ", text or "")
    return [t.lower() for t in text.split() if len(t) >= min_len]


def build_pdf_index(root: Path) -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = {}
    for year_dir in root.iterdir():
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        year = year_dir.name
        files = [f.name for f in year_dir.iterdir() if f.is_file() and f.name.lower().endswith('.pdf')]
        if files:
            mapping[year] = files
    return mapping


def score_filename(tokens: List[str], filename: str) -> Tuple[int, float]:
    lower = filename.lower()
    overlap = sum(1 for t in tokens if t in lower)
    density = overlap / max(len(tokens), 1)
    return overlap, density


def find_best(tokens: List[str], candidates: List[str]) -> Tuple[str, int, float] | None:
    best = None
    for fn in candidates:
        sc, dens = score_filename(tokens, fn)
        if sc == 0:
            continue
        if best is None or sc > best[1] or (sc == best[1] and dens > best[2]):
            best = (fn, sc, dens)
    return best


def enrich(es: Elasticsearch, index: str, pdf_root: Path, dry_run: bool, *, min_score: int, min_density: float, batch_size: int, force: bool, min_token_len: int):
    pdf_index = build_pdf_index(pdf_root)
    total_updates = 0
    # Scroll through documents
    resp = es.search(index=index, body={"query": {"match_all": {}}, "_source": ["case_name", "year", "pdf_filename"], "size": batch_size})
    scroll_id = resp.get('_scroll_id')
    hits = resp['hits']['hits']
    while hits:
        actions = []
        for h in hits:
            src = h.get('_source', {})
            if src.get('pdf_filename') and not force:
                continue  # already enriched
            case_name = src.get('case_name')
            year = src.get('year')
            tokens = tokenize(case_name or "", min_token_len)
            if len(tokens) < 2:
                continue
            # Candidate pool
            year_str = str(year) if year else None
            pool = []
            if year_str and year_str in pdf_index:
                pool = pdf_index[year_str]
            else:
                # all PDFs flattened (could be slow; optimize later)
                for lst in pdf_index.values():
                    pool.extend(lst)
            if not pool:
                continue
            best = find_best(tokens, pool)
            if not best:
                continue
            fn, sc, dens = best
            if sc < min_score or dens < min_density:
                continue
            chosen_year = year_str
            if not chosen_year:
                # attempt to infer year from filename prefix digits
                m = re.match(r"(19|20)\d{2}", fn)
                if m and m.group(0) in pdf_index:
                    chosen_year = m.group(0)
            if not chosen_year:
                # fallback: skip if year unknown for deterministic URL
                continue
            pdf_url = f"/pdfs/{chosen_year}/{fn}" if (pdf_root / chosen_year / fn).exists() else None
            doc_id = h['_id']
            if dry_run:
                print(f"DRY-RUN would update {doc_id}: pdf_filename={fn} score={sc} density={dens:.2f}")
            else:
                actions.append({
                    '_op_type': 'update',
                    '_index': index,
                    '_id': doc_id,
                    'doc': {
                        'pdf_filename': fn,
                        'pdf_url': pdf_url,
                        'pdf_match_score': sc,
                        'pdf_match_density': round(dens, 3)
                    }
                })
        if actions:
            helpers.bulk(es, actions)
            total_updates += len(actions)
        # Next scroll page
        scroll_id = resp.get('_scroll_id')
        if not scroll_id:
            break
        resp = es.scroll(scroll_id=scroll_id, scroll='2m')
        hits = resp['hits']['hits']
    print(f"Completed. Updated {total_updates} documents.")


def main():
    ap = argparse.ArgumentParser(description='Heuristically map case_name to local PDF files and update ES docs.')
    ap.add_argument('--pdf-root', default='data/supreme_court_judgments', help='Root directory containing year subfolders of PDFs')
    ap.add_argument('--host', default='http://localhost:9200', help='Elasticsearch host URL (can include basic auth)')
    ap.add_argument('--index', default='legit_search_index', help='Index name to enrich')
    ap.add_argument('--dry-run', action='store_true', help='Preview changes without updating ES')
    ap.add_argument('--commit', action='store_true', help='Alias for NOT dry-run (mutually exclusive with --dry-run)')
    ap.add_argument('--force', action='store_true', help='Re-evaluate docs even if pdf_filename already set')
    ap.add_argument('--min-score', type=int, default=MIN_SCORE_DEFAULT, help='Minimum overlapping token count')
    ap.add_argument('--min-density', type=float, default=MIN_DENSITY_DEFAULT, help='Minimum overlap density (overlap/num_tokens)')
    ap.add_argument('--min-token-len', type=int, default=MIN_TOKEN_LEN_DEFAULT, help='Minimum token length after normalization')
    ap.add_argument('--batch-size', type=int, default=BATCH_SIZE_DEFAULT, help='Scroll page size / bulk batch size')
    args = ap.parse_args()

    pdf_root = Path(args.pdf_root)
    if not pdf_root.exists():
        print(f"PDF root does not exist: {pdf_root}", file=sys.stderr)
        return 1
    es = Elasticsearch(args.host)
    if not es.indices.exists(index=args.index):
        print(f"Index not found: {args.index}", file=sys.stderr)
        return 1
    dry_run = args.dry_run or (not args.commit)
    enrich(
        es,
        args.index,
        pdf_root,
        dry_run,
        min_score=args.min_score,
        min_density=args.min_density,
        batch_size=args.batch_size,
        force=args.force,
        min_token_len=args.min_token_len,
    )
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
