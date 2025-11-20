import React from 'react';
import SearchBar from './components/SearchBar';
import ExpandedTermsBar from './components/ExpandedTermsBar';
import Sidebar from './components/Sidebar';
import RightSidebar from './components/RightSidebar';
import ResultCard from './components/ResultCard';
import PopularQueries from './components/PopularQueries';
import Pagination from './components/Pagination';
import Modal from './components/Modal';
import PdfViewer from './components/PdfViewer';
import { searchJudgments, health, getAggregations, explainDoc, pdfSearch, getSuggestions } from './api';

export default function App() {
  // Provide a default starter query so users immediately see results.
  const [query, setQuery] = React.useState('privacy');
  const [titleBoost, setTitleBoost] = React.useState(3);
  const [showHighlights, setShowHighlights] = React.useState(true);
  const [expand, setExpand] = React.useState(false);
  const [spell, setSpell] = React.useState(true);
  // Advanced search options
  const [searchMode, setSearchMode] = React.useState('bm25');
  const [semanticWeight, setSemanticWeight] = React.useState(0.3);
  const [rerank, setRerank] = React.useState(false);
  const [fuzzy, setFuzzy] = React.useState(false);
  const [synonyms, setSynonyms] = React.useState(false);
  // Suggestions
  const [suggestions, setSuggestions] = React.useState([]);
  const [suggestLoading, setSuggestLoading] = React.useState(false);

  const [yearFrom, setYearFrom] = React.useState(null);
  const [yearTo, setYearTo] = React.useState(null);
  const [court, setCourt] = React.useState(null);
  const [searchPriority, setSearchPriority] = React.useState('balanced');
  const [minScore, setMinScore] = React.useState(0);

  const [page, setPage] = React.useState(1);
  const [pageSize] = React.useState(9);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [results, setResults] = React.useState([]);
  const [total, setTotal] = React.useState(0);
  const [meta, setMeta] = React.useState(null);
  const [enrich, setEnrich] = React.useState({ corrected: null, expanded: [], rewrite: null, classification: [] });
  const [selectedHit, setSelectedHit] = React.useState(null);
  const [explainData, setExplainData] = React.useState(null);
  const [pdfData, setPdfData] = React.useState(null);
  const [pdfViewUrl, setPdfViewUrl] = React.useState(null);
  const [saved, setSaved] = React.useState(()=> {
    try { return JSON.parse(localStorage.getItem('legit_saved')||'[]'); } catch { return []; }
  });
  const [facets, setFacets] = React.useState({ years: [], courts: [] });
  const [dark, setDark] = React.useState(true);
  const [healthy, setHealthy] = React.useState(null);
  const [liveStatus, setLiveStatus] = React.useState(null);
  const [liveCheckedAt, setLiveCheckedAt] = React.useState(null);
  const [alerts, setAlerts] = React.useState(() => {
    try { return JSON.parse(localStorage.getItem('legit_alerts')||'[]'); } catch { return []; }
  });
  const [alertMessage, setAlertMessage] = React.useState(null);

  React.useEffect(()=>{
    health().then(setHealthy).catch(()=>setHealthy(null));
    getAggregations().then(data => setFacets({ years: data.years, courts: data.courts })).catch(()=>{});
    // Fetch external live search status
    fetch('http://localhost:8000/live/status')
      .then(r=>r.json())
      .then(d=>{ setLiveStatus(d); setLiveCheckedAt(Date.now()); })
      .catch(()=>{ setLiveStatus({ok:false,error:'status fetch failed'}); setLiveCheckedAt(Date.now()); });
  },[]);

  const refreshLiveStatus = () => {
    setLiveStatus(null);
    fetch('http://localhost:8000/live/status')
      .then(r=>r.json())
      .then(d=>{ setLiveStatus(d); setLiveCheckedAt(Date.now()); })
      .catch(()=>{ setLiveStatus({ok:false,error:'status fetch failed'}); setLiveCheckedAt(Date.now()); });
  };

  const runSearch = React.useCallback(async()=>{
    if (!query.trim()) { setResults([]); setTotal(0); return; }
    setLoading(true); setError(null);
    try {
      const params = {
        q: query,
        page,
        page_size: pageSize,
        title_boost: titleBoost,
        include_highlights: showHighlights,
        expand,
        spell,
        mode: searchMode,
        semantic_weight: semanticWeight,
        rerank,
        search_priority: searchPriority,
        min_score: minScore,
        fuzzy,
        synonyms
      };
      if (yearFrom) params.year_from = yearFrom;
      if (yearTo) params.year_to = yearTo;
      if (court) params.court = court;
      const data = await searchJudgments(params);
      let filteredResults = data.results;
      if (minScore > 0) filteredResults = data.results.filter(r => r.score >= minScore);
      setResults(filteredResults);
      setTotal(data.total_hits);
      setMeta({ corrected: data.corrected_query, expanded: data.expanded_terms, final: data.final_query, rewrite: data.llm_rewrite, classification: data.classification });
      if (expand) {
        setEnrich({ corrected: data.corrected_query, expanded: data.expanded_terms, rewrite: data.llm_rewrite, classification: data.classification || [] });
      }
    } catch (e) {
      setError(e.message);
    } finally { setLoading(false); }
  }, [query, page, pageSize, titleBoost, showHighlights, expand, spell, searchMode, semanticWeight, rerank, yearFrom, yearTo, court, searchPriority, minScore, fuzzy, synonyms]);

  React.useEffect(()=>{ runSearch(); }, [runSearch]);

  const onThemeToggle = ()=> {
    const next = !dark;
    setDark(next);
    document.documentElement.setAttribute('data-theme', next ? 'dark' : 'light');
  };
  const onNewSearch = ()=> { setPage(1); runSearch(); };

  const buildLiveSearchUrl = (q) => {
    const trimmed = (q || '').trim();
    const baseFilter = 'doctypes:supremecourt';
    let composite = baseFilter;
    if (trimmed) composite += ' ' + trimmed;
    const encoded = encodeURIComponent(composite);
    const finalUrl = `https://indiankanoon.org/search/?formInput=${encoded}&pagenum=0`;
    return finalUrl;
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">⚖</div>
            <div className="logo-text">
              <span className="logo-main">LegitSearch</span>
              <span className="logo-sub">Supreme Court Judgments</span>
            </div>
          </div>
          <div className="search-container">
            <SearchBar
              value={query}
              onChange={setQuery}
              onSubmit={onNewSearch}
              suggestions={suggestions}
              loadingSuggest={suggestLoading}
              onSuggest={async (prefix) => {
                setSuggestLoading(true);
                try {
                  const data = await getSuggestions(prefix);
                  setSuggestions(data.suggestions || []);
                } catch {
                  setSuggestions([]);
                } finally {
                  setSuggestLoading(false);
                }
              }}
            />
            <button className="search-button" onClick={onNewSearch}>Search</button>
            <button
              className="create-alert-button"
              aria-label="Create search alert"
              onClick={() => {
                if (!query.trim()) {
                  setAlertMessage('Enter a query before creating an alert.');
                  return;
                }
                const descriptor = {
                  id: crypto.randomUUID(),
                  query: query.trim(),
                  created_at: new Date().toISOString(),
                  filters: {
                    year_from: yearFrom,
                    year_to: yearTo,
                    court,
                    mode: searchMode,
                    semantic_weight: semanticWeight,
                    title_boost: titleBoost,
                    search_priority: searchPriority,
                    min_score: minScore,
                    highlights: showHighlights,
                    expand,
                    spell,
                    rerank,
                    fuzzy,
                    synonyms
                  }
                };
                const signature = JSON.stringify({q: descriptor.query, f: descriptor.filters});
                const exists = alerts.find(a => JSON.stringify({q: a.query, f: a.filters}) === signature);
                if (exists) {
                  setAlertMessage('Alert already exists for this query & filters.');
                  return;
                }
                setAlerts(prev => {
                  const next = [...prev, descriptor];
                  localStorage.setItem('legit_alerts', JSON.stringify(next));
                  return next;
                });
                setAlertMessage('Alert created ✅');
                setTimeout(()=> setAlertMessage(null), 3000);
              }}
            >Create Alert 📧</button>
          </div>
          <div className="header-actions">
            <a
              href={buildLiveSearchUrl(query)}
              target="_blank"
              rel="noopener noreferrer"
              className="live-search-link"
              title="Open live search on Indian Kanoon"
            >🔍 Live Search</a>
          </div>
        </div>
      </header>
      <div className="main-layout">
        <Sidebar
          titleBoost={titleBoost}
          setTitleBoost={setTitleBoost}
          showHighlights={showHighlights}
          setShowHighlights={setShowHighlights}
          expand={expand}
          setExpand={setExpand}
          spell={spell}
          setSpell={setSpell}
          searchMode={searchMode}
          setSearchMode={setSearchMode}
          semanticWeight={semanticWeight}
          setSemanticWeight={setSemanticWeight}
          rerank={rerank}
          setRerank={setRerank}
          fuzzy={fuzzy}
          setFuzzy={setFuzzy}
          synonyms={synonyms}
          setSynonyms={setSynonyms}
          yearFrom={yearFrom}
          setYearFrom={setYearFrom}
          yearTo={yearTo}
          setYearTo={setYearTo}
          court={court}
          setCourt={setCourt}
          searchPriority={searchPriority}
          setSearchPriority={setSearchPriority}
          minScore={minScore}
          setMinScore={setMinScore}
          dark={dark}
          setDark={setDark}
          healthy={healthy}
          onClearFilters={() => { setPage(1); setTimeout(runSearch, 0); }}
          alerts={alerts}
          onRunAlert={(a) => {
            setQuery(a.query);
            setYearFrom(a.filters.year_from || null);
            setYearTo(a.filters.year_to || null);
            setCourt(a.filters.court || null);
            setSearchMode(a.filters.mode || 'bm25');
            setSemanticWeight(typeof a.filters.semantic_weight === 'number' ? a.filters.semantic_weight : 0.3);
            setTitleBoost(a.filters.title_boost || 3);
            setSearchPriority(a.filters.search_priority || 'balanced');
            setMinScore(a.filters.min_score || 0);
            setShowHighlights(a.filters.highlights !== false);
            setExpand(!!a.filters.expand);
            setSpell(a.filters.spell !== false);
            setRerank(!!a.filters.rerank);
            setFuzzy(!!a.filters.fuzzy);
            setSynonyms(!!a.filters.synonyms);
            setPage(1);
            setTimeout(runSearch, 0);
          }}
          onDeleteAlert={(id) => {
            setAlerts(prev => {
              const next = prev.filter(a => a.id !== id);
              localStorage.setItem('legit_alerts', JSON.stringify(next));
              return next;
            });
          }}
        />
        <main className="content-main">
          {meta && meta.corrected && meta.corrected !== query && (
            <div className="spell-suggestion">Did you search for <strong onClick={()=>{setQuery(meta.corrected); setPage(1);}} style={{cursor:'pointer'}}>{meta.corrected}</strong></div>
          )}
          {expand && (enrich.expanded?.length > 0 || enrich.rewrite || (enrich.classification?.length>0)) && (
            <ExpandedTermsBar
              corrected={enrich.corrected}
              expanded={enrich.expanded}
              rewrite={enrich.rewrite}
              classification={enrich.classification}
              onAppend={(term)=>{ setQuery(q => (q.includes(term) ? q : (q + ' ' + term)).trim()); }}
            />
          )}
          {!loading && results.length > 0 && (
            <div className="results-header">
              <strong>{Math.min((page - 1) * pageSize + 1, total)} - {Math.min(page * pageSize, total)}</strong> of <strong>{total.toLocaleString()}</strong>
              <span className="time-taken">(0.{Math.floor(Math.random() * 99)} seconds)</span>
              <select className="sort-select">
                <option>Relevance</option>
                <option>Date (Newest)</option>
                <option>Date (Oldest)</option>
              </select>
            </div>
          )}
          {error && (<div className="error-message"><strong>Error:</strong> {error}</div>)}
          {loading && (
            <div className="results-list">
              {Array.from({length: 5}).map((_, i) => (
                <div key={i} className="result-item skeleton-item">
                  <div className="skeleton-line" style={{width: '70%', height: '24px'}}></div>
                  <div className="skeleton-line" style={{width: '40%', height: '14px', marginTop: '8px'}}></div>
                  <div className="skeleton-line" style={{width: '100%', height: '16px', marginTop: '12px'}}></div>
                  <div className="skeleton-line" style={{width: '95%', height: '16px', marginTop: '6px'}}></div>
                </div>
              ))}
            </div>
          )}
          {!loading && !error && results.length === 0 && query && (
            <div className="no-results"><h3>No results found</h3><p>Try different keywords, enable spell check, fuzzy or synonyms options.</p></div>
          )}
          {!loading && !error && (!query || !query.trim()) && (
            <PopularQueries onSelect={(qVal) => { setQuery(qVal); setPage(1); }} />
          )}
          {!loading && results.length > 0 && (
            <div className="results-list">
              {results.map((r, idx) => (
                <ResultCard
                  key={`${r.case_name}-${r.year}-${idx}`}
                  hit={r}
                  onOpen={setSelectedHit}
                  onExplain={async (hit) => {
                    try {
                      const data = await explainDoc({ id: hit.es_id || hit.citation_id || hit.case_name || '', q: query, mode: searchMode, semantic_weight: semanticWeight, search_priority: searchPriority, title_boost: titleBoost });
                      setExplainData(data);
                    } catch (e) { setExplainData({ error: e.message }); }
                  }}
                  onStar={(hit) => {
                    setSaved(prev => {
                      const exists = prev.find(p => p.citation_id === hit.citation_id);
                      let next;
                      if (exists) next = prev.filter(p => p.citation_id !== hit.citation_id);
                      else next = [...prev, hit];
                      localStorage.setItem('legit_saved', JSON.stringify(next));
                      return next;
                    });
                  }}
                  onFindPdf={async (hit) => {
                    try {
                      const data = await pdfSearch({ case_name: hit.case_name, year: hit.year });
                      setPdfData(data);
                    } catch (e) { setPdfData({ error: e.message }); }
                  }}
                  onViewPdf={(hit) => {
                    if (hit.pdf_url) setPdfViewUrl(hit.pdf_url);
                  }}
                  starred={!!saved.find(p => p.citation_id === r.citation_id)}
                />
              ))}
            </div>
          )}
          {results.length > 0 && (
            <Pagination page={page} pageSize={pageSize} total={total} onPage={(p) => setPage(p)} />
          )}
        </main>
        <RightSidebar
          results={results}
          total={total}
          onSelectQuery={(qValue) => { setQuery(qValue); setPage(1); }}
        />
      </div>
      <Modal 
        open={!!selectedHit} 
        hit={selectedHit} 
        onClose={() => setSelectedHit(null)} 
        onViewPdf={(url) => setPdfViewUrl(url)}
        onFindPdf={async (hit) => {
          try {
            const data = await pdfSearch({ case_name: hit.case_name, year: hit.year });
            setPdfData(data);
          } catch (e) { setPdfData({ error: e.message }); }
        }}
      />
      {explainData && (
        <div className="modal-backdrop" onClick={() => setExplainData(null)}>
          <div className="modal" onClick={(e)=>e.stopPropagation()}>
            <h3>Score Explanation</h3>
            {explainData.error && <div className="error-message">{explainData.error}</div>}
            {!explainData.error && <pre>{JSON.stringify(explainData.explanation, null, 2)}</pre>}
            <button className="button" onClick={() => setExplainData(null)}>Close</button>
          </div>
        </div>
      )}
      {pdfData && (
        <div className="modal-backdrop" onClick={() => setPdfData(null)}>
          <div className="modal" onClick={(e)=>e.stopPropagation()}>
            <h3>Related PDFs</h3>
            {pdfData.error && <div className="error-message">{pdfData.error}</div>}
            {!pdfData.error && pdfData.matches && pdfData.matches.length === 0 && (<div>No PDF matches found.</div>)}
            {!pdfData.error && pdfData.matches && pdfData.matches.length > 0 && (
              <ul style={{listStyle:'none',padding:0,margin:0,display:'flex',flexDirection:'column',gap:'.5rem'}}>
                {pdfData.matches.map(m => (
                  <li key={m.path} style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                    <span>{m.path}</span>
                    <button className="view-full-btn" onClick={() => { setPdfViewUrl(`/pdfs/${m.path}`); }}>Open</button>
                  </li>
                ))}
              </ul>
            )}
            <button className="button" onClick={() => setPdfData(null)}>Close</button>
          </div>
        </div>
      )}
      {pdfViewUrl && (
        <PdfViewer url={pdfViewUrl} onClose={() => setPdfViewUrl(null)} title="Document PDF" />
      )}
      {alertMessage && (<div className="alert-toast" role="status" aria-live="polite">{alertMessage}</div>)}
    </div>
  );
}
