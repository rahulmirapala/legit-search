import React from 'react';

export default function ExpandedTermsBar({ corrected, expanded, rewrite, classification, onAppend }) {
  if (!expanded?.length && !rewrite && !classification?.length) return null;
  return (
    <div className="expanded-bar" aria-label="Expanded query terms">
      {corrected && corrected !== rewrite && corrected !== '' && (
        <span className="expanded-chip corrected" title="Spell-corrected base" onClick={()=>onAppend(corrected)}>{corrected}</span>
      )}
      {rewrite && (
        <span className="expanded-chip rewrite" title="LLM rewrite" onClick={()=>onAppend(rewrite)}>{rewrite}</span>
      )}
      {classification && classification.map(c => (
        <span key={c} className="expanded-chip class" title="Category label" onClick={()=>onAppend(c)}>{c}</span>
      ))}
      {expanded && expanded.map(t => (
        <span key={t} className="expanded-chip term" onClick={()=>onAppend(t)}>{t}</span>
      ))}
    </div>
  );
}
