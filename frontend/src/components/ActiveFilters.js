import React from 'react';

export default function ActiveFilters({ 
  searchMode, 
  searchPriority, 
  yearFrom, 
  yearTo, 
  court, 
  minScore,
  rerank,
  semanticWeight
}) {
  const activeFilters = [];
  
  if (searchMode !== 'bm25') {
    activeFilters.push({
      label: `Mode: ${searchMode}`,
      value: searchMode === 'hybrid' ? `${(semanticWeight * 100).toFixed(0)}% semantic` : 'semantic'
    });
  }
  
  if (searchPriority !== 'balanced') {
    activeFilters.push({
      label: `Priority: ${searchPriority}`,
      value: searchPriority
    });
  }
  
  if (yearFrom || yearTo) {
    const yearRange = `${yearFrom || '1950'}–${yearTo || '2025'}`;
    activeFilters.push({
      label: 'Years',
      value: yearRange
    });
  }
  
  if (court) {
    activeFilters.push({
      label: 'Court',
      value: court
    });
  }
  
  if (minScore > 0) {
    activeFilters.push({
      label: 'Min Score',
      value: `≥${minScore}`
    });
  }
  
  if (rerank) {
    activeFilters.push({
      label: 'Reranking',
      value: 'enabled'
    });
  }
  
  if (activeFilters.length === 0) return null;
  
  return (
    <div className="active-filters">
      <span className="filters-label">Active Filters:</span>
      {activeFilters.map((filter, idx) => (
        <span key={idx} className="filter-tag">
          <strong>{filter.label}:</strong> {filter.value}
        </span>
      ))}
    </div>
  );
}
