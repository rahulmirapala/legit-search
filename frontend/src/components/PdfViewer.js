import React from 'react';

// Resolve API base dynamically (supports dev proxy or env override)
const API_BASE = (typeof process !== 'undefined' && process.env.REACT_APP_API_BASE) || 'http://localhost:8000';

export default function PdfViewer({ url, onClose, title }) {
  const [error, setError] = React.useState(false);
  if (!url) return null;
  const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal pdf-modal" onClick={(e)=>e.stopPropagation()} style={{width:'90vw', height:'90vh', display:'flex', flexDirection:'column'}}>
        <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'.5rem'}}>
          <div style={{display:'flex', gap:'.75rem', alignItems:'center'}}>
            <span style={{fontWeight:600}}>{title || 'PDF Viewer'}</span>
            <a href={fullUrl} target="_blank" rel="noopener noreferrer" className="view-full-btn">Open Tab</a>
            <a href={fullUrl} download className="view-full-btn">Download</a>
          </div>
          <button className="button" onClick={onClose}>Close</button>
        </div>
        {!error && (
          <iframe
            title={title || 'PDF'}
            src={fullUrl}
            style={{flex:1, border:'none', background:'#111'}}
            onError={() => setError(true)}
          />
        )}
        {error && (
          <div style={{flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:'1rem'}}>
            <p style={{color:'#f55', fontWeight:600}}>Failed to load PDF inline.</p>
            <a href={fullUrl} target="_blank" rel="noopener noreferrer" className="view-full-btn">Open in new tab</a>
          </div>
        )}
      </div>
    </div>
  );
}
