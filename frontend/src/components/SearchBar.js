import React from 'react';
import debounce from 'lodash.debounce';

export default function SearchBar({ value, onChange, onSubmit, suggestions = [], onSuggest = () => {}, loadingSuggest = false }) {
  const [open, setOpen] = React.useState(false);

  const debounced = React.useMemo(() => debounce((val) => {
    if (val && val.length >= 3) {
      onSuggest(val);
      setOpen(true);
    } else {
      setOpen(false);
    }
  }, 250), [onSuggest]);

  const handleChange = (e) => {
    const val = e.target.value;
    onChange(val);
    debounced(val);
  };

  return (
    <div className="search-box" role="search">
      <span className="icon">🔍</span>
      <input
        autoFocus
        type="text"
        placeholder="Search judgments (e.g. fundamental rights)"
        value={value}
        onChange={handleChange}
        onKeyDown={(e)=>{ if(e.key==='Enter'){ onSubmit(); setOpen(false); } }}
        aria-label="Search judgments"
        onBlur={()=> setTimeout(()=> setOpen(false), 120)}
        onFocus={()=> { if(value && value.length>=3 && suggestions.length>0) setOpen(true); }}
      />
      {open && (
        <ul className="suggest-dropdown" role="listbox">
          {loadingSuggest && <li className="suggest-item">Loading...</li>}
          {!loadingSuggest && suggestions.slice(0, 8).map(s => (
            <li
              key={s}
              className="suggest-item"
              onMouseDown={(e)=>{ e.preventDefault(); onChange(s); onSubmit(); setOpen(false); }}
              role="option"
            >{s}</li>
          ))}
          {!loadingSuggest && suggestions.length === 0 && <li className="suggest-item">No suggestions</li>}
        </ul>
      )}
    </div>
  );
}
