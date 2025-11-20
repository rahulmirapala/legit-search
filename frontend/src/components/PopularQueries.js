import React from 'react';

const PRESET_QUERIES = [
  'privacy',
  'fundamental rights',
  'judicial review',
  'reservation',
  'basic structure',
  'writ petition',
  'equality before law'
];

export default function PopularQueries({ onSelect }) {
  return (
    <div className="popular-queries-panel">
      <h3>Popular Queries</h3>
      <p>Try one of these to explore the corpus:</p>
      <div className="popular-query-list">
        {PRESET_QUERIES.map(q => (
          <button
            key={q}
            className="popular-query-btn"
            onClick={() => onSelect(q)}
            aria-label={`Run query ${q}`}
          >{q}</button>
        ))}
      </div>
    </div>
  );
}