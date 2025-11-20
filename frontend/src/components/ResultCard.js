import React from 'react';

export default function ResultCard({ hit, onOpen, onExplain, onStar, starred, onFindPdf, onViewPdf }) {
  const excerpt = hit.highlights && hit.highlights.length > 0 
    ? hit.highlights[0] 
    : hit.full_text?.substring(0, 200) + '...';

  return (
    <div className="result-item">
      <h3 className="result-title">
        <a href="#" onClick={(e) => { e.preventDefault(); onOpen(hit); }}>
          {hit.case_name || 'Untitled'}
        </a>
      </h3>
      
      <div className="result-meta">
        <span className="meta-court">Supreme Court of India</span>
        {hit.judgment_date && (
          <>
            <span className="meta-separator">-</span>
            <span className="meta-date">{new Date(hit.judgment_date).toLocaleDateString('en-IN', { 
              day: 'numeric', 
              month: 'long', 
              year: 'numeric' 
            })}</span>
          </>
        )}
      </div>

      <div className="result-excerpt" dangerouslySetInnerHTML={{ __html: excerpt }} />

      <div className="result-footer">
        <div className="footer-left">
          <button
            className={`star-btn ${starred ? 'starred' : ''}`}
            title={starred ? 'Remove from saved' : 'Save result'}
            onClick={() => onStar && onStar(hit)}
          >
            {starred ? '★ Saved' : '☆ Save'}
          </button>
          <button
            className="explain-btn"
            title={hit.es_id ? 'Explain relevance score' : 'Explanation unavailable (missing id)'}
            disabled={!hit.es_id}
            onClick={() => hit.es_id && onExplain && onExplain(hit)}
          >
            ℹ Explain
          </button>
        </div>
        <div className="footer-right">
          <span className="relevance-score">
            Relevance: {hit.score?.toFixed(2) || 'N/A'}
          </span>
          {hit.pdf_url ? (
            <>
              <button className="view-full-btn" title="View PDF inline" onClick={() => onViewPdf && onViewPdf(hit)}>
                📄 View
              </button>
              <a className="view-full-btn" href={`http://localhost:8000${hit.pdf_url}`} target="_blank" rel="noopener noreferrer" title="Open PDF in new tab">↗ Tab</a>
            </>
          ) : (
            <button className="view-full-btn" title="Find matching PDF" onClick={() => onFindPdf && onFindPdf(hit)}>
              📄 Find PDF
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

