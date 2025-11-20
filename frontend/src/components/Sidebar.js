import React from 'react';

export default function Sidebar({ 
  titleBoost, setTitleBoost,
  showHighlights, setShowHighlights,
  expand, setExpand,
  spell, setSpell,
  searchMode, setSearchMode,
  semanticWeight, setSemanticWeight,
  rerank, setRerank,
  fuzzy, setFuzzy,
  synonyms, setSynonyms,
  yearFrom, setYearFrom,
  yearTo, setYearTo,
  court, setCourt,
  searchPriority, setSearchPriority,
  minScore, setMinScore,
  dark, setDark,
  healthy,
  onClearFilters,
  alerts = [],
  onRunAlert = () => {},
  onDeleteAlert = () => {}
}) {
  const onThemeToggle = () => {
    setDark(d => !d);
    document.documentElement.setAttribute('data-theme', dark ? 'light' : 'dark');
  };

  return (
    <aside className="sidebar-left">
      <h2>Filter Results by</h2>
      
      {/* Document Types */}
      <div className="filter-section">
        <h3 className="filter-heading">Document Types</h3>
        <label className="filter-option">
          <input type="radio" name="doctype" defaultChecked /> All
        </label>
        <label className="filter-option">
          <input type="radio" name="doctype" /> Judgments
        </label>
        <label className="filter-option">
          <input type="radio" name="doctype" /> Laws
        </label>
      </div>

      {/* Courts */}
      <div className="filter-section">
        <h3 className="filter-heading">Courts and Laws</h3>
        <select 
          value={court || ''} 
          onChange={(e) => setCourt(e.target.value || null)} 
          className="filter-select-compact"
        >
          <option value="">All Courts</option>
          <option value="Supreme Court">Supreme Court of India</option>
          <option value="High Court">High Courts</option>
          <option value="District Court">District Courts</option>
        </select>
      </div>

      {/* Year Range */}
      <div className="filter-section">
        <h3 className="filter-heading">Year Range</h3>
        <div className="year-range-inputs">
          <input 
            type="number" 
            placeholder="From" 
            value={yearFrom || ''} 
            onChange={(e) => setYearFrom(e.target.value ? Number(e.target.value) : null)}
            className="year-input-compact"
            min="1950"
            max="2025"
          />
          <span>—</span>
          <input 
            type="number" 
            placeholder="To" 
            value={yearTo || ''} 
            onChange={(e) => setYearTo(e.target.value ? Number(e.target.value) : null)}
            className="year-input-compact"
            min="1950"
            max="2025"
          />
        </div>
      </div>

      {/* Search Mode */}
      <div className="filter-section">
        <h3 className="filter-heading">Search Mode</h3>
        <select 
          value={searchMode} 
          onChange={(e) => setSearchMode(e.target.value)} 
          className="filter-select-compact"
        >
          <option value="bm25">BM25 (Keyword)</option>
          <option value="hybrid">Hybrid (BM25 + Semantic)</option>
          <option value="semantic">Semantic Only</option>
        </select>
        {searchMode === 'hybrid' && (
          <div className="slider-control">
            <label>Semantic Weight: {(semanticWeight * 100).toFixed(0)}%</label>
            <input 
              type="range" 
              min={0} 
              max={1} 
              step={0.1} 
              value={semanticWeight} 
              onChange={(e) => setSemanticWeight(Number(e.target.value))}
              className="slider"
            />
          </div>
        )}
      </div>

      {/* Search Priority */}
      <div className="filter-section">
        <h3 className="filter-heading">Search Priority</h3>
        <select 
          value={searchPriority} 
          onChange={(e) => setSearchPriority(e.target.value)} 
          className="filter-select-compact"
        >
          <option value="balanced">Balanced</option>
          <option value="heading">Heading/Title</option>
          <option value="introduction">Introduction</option>
          <option value="body">Body/Arguments</option>
          <option value="conclusion">Conclusion</option>
        </select>
      </div>

      {/* Boost Settings */}
      <div className="filter-section">
        <h3 className="filter-heading">Boost Settings</h3>
        <div className="slider-control">
          <label>Title Boost: {titleBoost.toFixed(1)}x</label>
          <input 
            type="range" 
            min={1} 
            max={10} 
            value={titleBoost} 
            onChange={(e) => setTitleBoost(Number(e.target.value))}
            className="slider"
          />
        </div>
        <div className="slider-control">
          <label>Min Score: {minScore.toFixed(1)}</label>
          <input 
            type="range" 
            min={0} 
            max={10} 
            step={0.5} 
            value={minScore} 
            onChange={(e) => setMinScore(Number(e.target.value))}
            className="slider"
          />
        </div>
      </div>

      {/* Options */}
      <div className="filter-section">
        <h3 className="filter-heading">Options</h3>
        <label className="filter-checkbox">
          <input type="checkbox" checked={showHighlights} onChange={(e) => setShowHighlights(e.target.checked)} />
          <span>Show Highlights</span>
        </label>
        <label className="filter-checkbox">
          <input type="checkbox" checked={spell} onChange={(e) => setSpell(e.target.checked)} />
          <span>Spell Check</span>
        </label>
        <label className="filter-checkbox">
          <input type="checkbox" checked={expand} onChange={(e) => setExpand(e.target.checked)} />
          <span>LLM Expansion</span>
        </label>
        <label className="filter-checkbox">
          <input type="checkbox" checked={rerank} onChange={(e) => setRerank(e.target.checked)} />
          <span>Reranking</span>
        </label>
        <label className="filter-checkbox">
          <input type="checkbox" checked={fuzzy} onChange={(e) => setFuzzy(e.target.checked)} />
          <span>Fuzzy Match</span>
        </label>
        <label className="filter-checkbox">
          <input type="checkbox" checked={synonyms} onChange={(e) => setSynonyms(e.target.checked)} />
          <span>Synonyms</span>
        </label>
      </div>

      {/* Clear Filters */}
      <div className="filter-section">
        <h3 className="filter-heading">Reset</h3>
        <button
          className="clear-filters-btn"
          onClick={() => {
            setYearFrom(null);
            setYearTo(null);
            setCourt(null);
            setMinScore(0);
            setSearchPriority('balanced');
            setTitleBoost(3);
            setSemanticWeight(0.3);
            if (onClearFilters) onClearFilters();
          }}
        >
          🔄 Clear Filters
        </button>
      </div>

      {/* Theme Toggle */}
      <div className="sidebar-footer">
        <button className="theme-toggle-btn" onClick={onThemeToggle}>
          {dark ? '🌙 Dark Mode' : '☀️ Light Mode'}
        </button>
        {healthy && (
          <div className="health-status">
            ES: {healthy.elasticsearch} • Docs: 26,688
          </div>
        )}
        {alerts.length > 0 && (
          <div className="alerts-section" aria-label="Saved alerts">
            <h3 className="filter-heading">Alerts ({alerts.length})</h3>
            <div className="alerts-list">
              {alerts.map(a => (
                <div key={a.id} className="alert-item">
                  <button className="alert-run-btn" aria-label={`Run alert for ${a.query}`} onClick={() => onRunAlert(a)}>{a.query.slice(0,30)}{a.query.length>30?'…':''}</button>
                  <button className="alert-delete-btn" aria-label="Delete alert" onClick={() => onDeleteAlert(a.id)}>✖</button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
