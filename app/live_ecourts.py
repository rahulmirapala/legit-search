"""Live querying utilities for Indian Supreme Court judgments.

Since eCourts portal uses heavy JavaScript/AJAX, we use Indian Kanoon instead,
which provides reliable HTML-based search for Supreme Court judgments.

WARNING: This is a best-effort HTML scraper. The site may change its DOM.
Use sparingly and cache results to avoid load on the public site.
"""
from __future__ import annotations
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
import time

INDIAN_KANOON_BASE = "https://indiankanoon.org"
SEARCH_PATH = "/search/"
# Search specifically for Supreme Court judgments

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

class LiveSearchError(Exception):
    pass

async def fetch_html(client: httpx.AsyncClient, url: str, params: dict) -> str:
    resp = await client.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
    if resp.status_code != 200:
        raise LiveSearchError(f"Upstream returned {resp.status_code}")
    return resp.text

def _extract_results(soup: BeautifulSoup) -> List[Dict]:
    """Extract search results from Indian Kanoon HTML."""
    results: List[Dict] = []
    
    # Indian Kanoon uses <div class="result"> for each search result
    for result_div in soup.select('div.result'):
        # Title is in <a> with class cite_tag or similar
        title_link = result_div.find('a', href=True)
        if not title_link:
            continue
            
        case_title = title_link.get_text(strip=True)
        href = title_link['href']
        
        # Normalize URL
        if href.startswith('/'):
            full_url = INDIAN_KANOON_BASE + href
        elif href.startswith('http'):
            full_url = href
        else:
            full_url = INDIAN_KANOON_BASE + '/' + href
        
        # Extract snippet - usually in <div class="result_title"> or subsequent text
        snippet_text = result_div.get_text(" ", strip=True)[:500]
        
        # Try to extract date from snippet
        date_match = re.search(r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})', snippet_text, re.IGNORECASE)
        judgment_date = date_match.group(1) if date_match else None
        
        # Extract citation if present
        citation_match = re.search(r'(\d{4}\s+\w+\s+\d+|AIR\s+\d{4}\s+SC\s+\d+|\(\d{4}\)\s+\d+\s+SCC\s+\d+)', snippet_text)
        citation = citation_match.group(1) if citation_match else None
        
        results.append({
            "case_title": case_title,
            "citation": citation,
            "judgment_date_raw": judgment_date,
            "source_url": full_url,
            "snippet": snippet_text
        })
    
    return results

async def live_supreme_search(query: str, limit: int = 5, year: Optional[int] = None) -> Dict:
    """Perform a live search for Supreme Court judgments using Indian Kanoon.

    Parameters
    ----------
    query: str - keyword(s) to search
    limit: int - max number of results to return
    year: Optional[int] - optional year filter
    """
    if not query.strip():
        return {"query": query, "results": [], "error": "Empty query"}

    # Construct search URL for Supreme Court documents
    # Indian Kanoon format: /search/?formInput=doctypes:supremecourt query terms year:YYYY
    search_query = f"doctypes:supremecourt {query}"
    if year:
        search_query += f" year:{year}"
    
    params = {
        'formInput': search_query,
        'pagenum': 0
    }

    async with httpx.AsyncClient(base_url=INDIAN_KANOON_BASE, headers={"User-Agent": USER_AGENT}) as client:
        start = time.time()
        try:
            html = await fetch_html(client, SEARCH_PATH, params=params)
        except Exception as e:
            return {"query": query, "results": [], "error": f"Fetch failed: {e}"}

    soup = BeautifulSoup(html, 'lxml')
    extracted = _extract_results(soup)

    # Deduplicate by source_url
    seen = set()
    deduped = []
    for r in extracted:
        if r['source_url'] in seen:
            continue
        seen.add(r['source_url'])
        deduped.append(r)
        if len(deduped) >= limit:
            break

    duration_ms = round((time.time() - start) * 1000, 2)
    return {
        "query": query,
        "year": year,
        "limit": limit,
        "duration_ms": duration_ms,
        "result_count": len(deduped),
        "results": deduped,
        "source": "Indian Kanoon (indiankanoon.org)",
        "notice": "Live search results from public database. May not reflect latest judgments." if deduped else "No results found. Try different keywords."
    }

# Synchronous helper for testing (optional)
def live_supreme_search_sync(query: str, limit: int = 5, year: Optional[int] = None) -> Dict:
    import asyncio
    return asyncio.run(live_supreme_search(query, limit=limit, year=year))
