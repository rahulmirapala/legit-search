import React from 'react';

export default function Pagination({ page, pageSize, total, onPage }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const canPrev = page > 1;
  const canNext = page < totalPages;

  return (
    <div className="pagination" aria-label="Pagination controls">
      <button className="button secondary" disabled={!canPrev} onClick={()=>onPage(page-1)}>Prev</button>
      <span style={{padding:'.6rem .9rem', background:'var(--bg-alt)', borderRadius:'var(--radius-md)'}}>{page} / {totalPages}</span>
      <button className="button secondary" disabled={!canNext} onClick={()=>onPage(page+1)}>Next</button>
    </div>
  );
}
