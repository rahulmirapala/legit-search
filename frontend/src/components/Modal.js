import React from 'react';

export default function Modal({ open, onClose, hit, onViewPdf, onFindPdf }) {
  if (!open || !hit) return null;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e)=>e.stopPropagation()} role="dialog" aria-modal="true">
        <h2 style={{margin:0}}>{hit.case_name}</h2>
        <div className="meta" style={{marginBottom:'.5rem'}}>{hit.judgment_date} • {hit.citation_id}</div>
        <div style={{display:'flex',gap:'.5rem',flexWrap:'wrap'}}>
          {hit.highlights?.map((h,i)=>(<div key={i} className="highlight-fragment" dangerouslySetInnerHTML={{__html: h}} />))}
        </div>
        <div style={{display:'flex', gap:'.5rem', marginTop:'.75rem'}}>
          {hit.pdf_url && (
            <button className="view-full-btn" onClick={()=> onViewPdf && onViewPdf(hit.pdf_url)}>📄 View PDF</button>
          )}
          {!hit.pdf_url && (
            <button className="view-full-btn" onClick={()=> onFindPdf && onFindPdf(hit)}>📄 Find PDF</button>
          )}
        </div>
        <button className="button secondary" onClick={onClose}>Close</button>
      </div>
    </div>
  );
}
