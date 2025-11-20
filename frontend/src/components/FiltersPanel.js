import React from 'react';

export default function FiltersPanel({ 
  titleBoost, setTitleBoost, 
  showHighlights, setShowHighlights, 
  expand, setExpand, 
  spell, setSpell,
  searchMode, setSearchMode,
  semanticWeight, setSemanticWeight,
  rerank, setRerank,
  yearFrom, setYearFrom,
  yearTo, setYearTo,
  court, setCourt,
  searchPriority, setSearchPriority,
  minScore, setMinScore
}) {
  return (
    <div className="filters-group" aria-label="Search filters">
      {/* Search Mode */}
      <div className="filter-section">
        <label className="section-label">Search Mode</label>
        <div className="filter-row">
          <select value={searchMode} onChange={(e)=>setSearchMode(e.target.value)} className="filter-select">
            <option value="bm25">BM25 (Keyword)</option>
            <option value="hybrid">Hybrid (BM25 + Semantic)</option>
            <option value="semantic">Semantic Only</option>
          </select>
        </div>
        {searchMode === 'hybrid' && (
          <div className="filter-row">
            <label>Semantic Weight</label>
            <input type="range" min={0} max={1} step={0.1} value={semanticWeight} 
              onChange={(e)=>setSemanticWeight(Number(e.target.value))} />
            <small>{(semanticWeight * 100).toFixed(0)}%</small>
          </div>
        )}
      </div>

      {/* Search Priority (Document Sections) */}
      <div className="filter-section">
        <label className="section-label">Search Priority</label>
        <div className="filter-row">
          <select value={searchPriority} onChange={(e)=>setSearchPriority(e.target.value)} className="filter-select">
            <option value="balanced">Balanced (All Sections)</option>
            <option value="heading">Heading/Title Priority</option>
            <option value="introduction">Introduction Priority</option>
            <option value="body">Body/Arguments Priority</option>
            <option value="conclusion">Conclusion/Judgment Priority</option>
          </select>
        </div>
      </div>

      {/* Boost Controls */}
      <div className="filter-section">
        <label className="section-label">Boost Settings</label>
        <div className="filter-row">
          <label>Title Boost</label>
          <input type="range" min={1} max={10} value={titleBoost} 
            onChange={(e)=>setTitleBoost(Number(e.target.value))} />
          <small>{titleBoost.toFixed(1)}x</small>
        </div>
        <div className="filter-row">
          <label>Min Score</label>
          <input type="range" min={0} max={10} step={0.5} value={minScore} 
            onChange={(e)=>setMinScore(Number(e.target.value))} />
          <small>{minScore.toFixed(1)}</small>
        </div>
      </div>

      {/* Year Filter */}
      <div className="filter-section">
        <label className="section-label">Year Range</label>
        <div className="filter-row" style={{display: 'flex', gap: '0.5rem', alignItems: 'center'}}>
          <input 
            type="number" 
            placeholder="From" 
            value={yearFrom || ''} 
            onChange={(e)=>setYearFrom(e.target.value ? Number(e.target.value) : null)}
            className="year-input"
            min="1950"
            max="2025"
          />
          <span>—</span>
          <input 
            type="number" 
            placeholder="To" 
            value={yearTo || ''} 
            onChange={(e)=>setYearTo(e.target.value ? Number(e.target.value) : null)}
            className="year-input"
            min="1950"
            max="2025"
          />
        </div>
      </div>

      {/* Court Filter */}
      <div className="filter-section">
        <label className="section-label">Court</label>
        <div className="filter-row">
          <select value={court || ''} onChange={(e)=>setCourt(e.target.value || null)} className="filter-select">
            <option value="">All Courts</option>
            <option value="Supreme Court">Supreme Court</option>
            <option value="High Court">High Court</option>
            <option value="District Court">District Court</option>
          </select>
        </div>
      </div>

      {/* Advanced Options */}
      <div className="filter-section">
        <label className="section-label">Options</label>
        <div className="filter-row">
          <label className="filter-inline">
            <input type="checkbox" checked={showHighlights} onChange={(e)=>setShowHighlights(e.target.checked)} /> 
            Highlights
          </label>
          <label className="filter-inline">
            <input type="checkbox" checked={expand} onChange={(e)=>setExpand(e.target.checked)} /> 
            Expand (LLM)
          </label>
        </div>
        <div className="filter-row">
          <label className="filter-inline">
            <input type="checkbox" checked={spell} onChange={(e)=>setSpell(e.target.checked)} /> 
            Spell Check
          </label>
          <label className="filter-inline">
            <input type="checkbox" checked={rerank} onChange={(e)=>setRerank(e.target.checked)} /> 
            Rerank
          </label>
        </div>
      </div>
    </div>
  );
}
