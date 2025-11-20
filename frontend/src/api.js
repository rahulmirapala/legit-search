// Simple API client abstraction
// Smart base resolution:
// 1. REACT_APP_API_BASE overrides all.
// 2. If running in local dev (port 3000) talk directly to backend at :8000.
// 3. Otherwise (production container with nginx proxy) use relative '/api'.
const API_BASE = (process.env.REACT_APP_API_BASE ||
  (typeof window !== 'undefined' && window.location.port === '3000'
    ? 'http://localhost:8000'
    : '/api'));

function buildUrl(path, params = {}) {
  // Ensure leading slash so URL resolves correctly for relative '/api' base
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  // If API_BASE already absolute (http...), use URL constructor; else concatenate for relative proxy.
  let full;
  if (/^https?:/i.test(API_BASE)) {
    full = new URL(normalizedPath, API_BASE);
  } else {
    full = new URL(normalizedPath, window.location.origin + API_BASE.replace(/\/$/, ''));
  }
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') full.searchParams.set(k, v);
  });
  return full.toString();
}

// Extended search function supporting advanced parameters.
// Any new backend parameter can be passed through this options object.
export async function searchJudgments(options) {
  const {
    q,
    page = 1,
    page_size = 9,
    title_boost = 3,
    include_highlights = true,
    expand = false,
    spell = true,
    mode = 'bm25',
    semantic_weight = 0.3,
    rerank = false,
    year_from,
    year_to,
    court,
    search_priority = 'balanced',
    min_score = 0,
    fuzzy = false,
    synonyms = false
  } = options;

  const url = buildUrl('/search', {
    q,
    page,
    page_size,
    title_boost,
    include_highlights,
    expand,
    spell,
    mode,
    semantic_weight,
    rerank,
    year_from,
    year_to,
    court,
    search_priority,
    min_score,
    fuzzy,
    synonyms
  });

  const res = await fetch(url);
  if (!res.ok) {
    // Try to parse JSON error if available
    let detail = '';
    try { detail = (await res.json()).message || ''; } catch (_) {}
    throw new Error(`Search failed (${res.status}) ${detail}`.trim());
  }
  return res.json();
}

export async function enrichQuery(q) {
  // Hits search endpoint with expand=true but minimal page size to get expansions only (alternate approach could be a dedicated endpoint)
  const data = await searchJudgments({ q, page: 1, page_size: 1, expand: true, spell: true });
  return {
    corrected: data.corrected_query,
    expanded: data.expanded_terms,
    rewrite: data.llm_rewrite,
    classification: data.classification
  };
}

export async function health() {
  const res = await fetch(buildUrl('/health'));
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function metricsRaw() {
  const res = await fetch(buildUrl('/metrics'));
  if (!res.ok) throw new Error('Metrics fetch failed');
  return res.text();
}

export async function getAggregations() {
  const res = await fetch(buildUrl('/aggregations'));
  if (!res.ok) throw new Error('Aggregations failed');
  return res.json();
}

export async function getStats() {
  const res = await fetch(buildUrl('/stats'));
  if (!res.ok) throw new Error('Stats failed');
  return res.json();
}

export async function explainDoc({ id, q, title_boost = 3, search_priority = 'balanced', mode = 'bm25', semantic_weight = 0.3 }) {
  const url = buildUrl(`/explain/${id}`, { q, title_boost, search_priority, mode, semantic_weight });
  const res = await fetch(url);
  let data;
  try { data = await res.json(); } catch { data = null; }
  if (!res.ok) {
    const detail = data?.detail || data?.message || `HTTP ${res.status}`;
    throw new Error(`Explain failed: ${detail}`);
  }
  return data;
}

export async function pdfSearch({ case_name, year }) {
  const url = buildUrl('/pdf/search', { case_name, year });
  const res = await fetch(url);
  if (!res.ok) throw new Error('PDF search failed');
  return res.json();
}

export async function getSuggestions(prefix) {
  const url = buildUrl('/suggest', { prefix });
  const res = await fetch(url);
  if (!res.ok) throw new Error('Suggest failed');
  return res.json();
}
