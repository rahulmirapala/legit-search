import React from 'react';

export default function RightSidebar({ results, total, onSelectQuery }) {
  // Extract top legal concepts/tags from results
  const extractTags = () => {
    const tags = new Map();
    
    results.forEach(result => {
      const text = (result.case_name + ' ' + result.full_text?.substring(0, 500) || '').toLowerCase();
      
      // Common legal concepts
      const concepts = [
        { name: 'fundamental-rights', label: 'Fundamental Rights', pattern: /fundamental\s+rights?/g },
        { name: 'writ-petition', label: 'Writ Petition', pattern: /writ\s+petition/g },
        { name: 'constitutional-law', label: 'Constitutional Law', pattern: /constitution/g },
        { name: 'public-interest', label: 'Public Interest', pattern: /public\s+interest/g },
        { name: 'natural-justice', label: 'Natural Justice', pattern: /natural\s+justice/g },
        { name: 'supreme-court', label: 'Supreme Court', pattern: /supreme\s+court/g },
        { name: 'high-court', label: 'High Court', pattern: /high\s+court/g },
        { name: 'criminal-law', label: 'Criminal Law', pattern: /criminal|penal/g },
        { name: 'civil-law', label: 'Civil Law', pattern: /civil\s+(suit|proceeding)/g },
        { name: 'contract', label: 'Contract Law', pattern: /contract/g },
        { name: 'property', label: 'Property Law', pattern: /property/g },
        { name: 'taxation', label: 'Taxation', pattern: /tax|taxation/g },
        { name: 'labour', label: 'Labour Law', pattern: /labour|employment/g },
      ];
      
      concepts.forEach(concept => {
        const matches = text.match(concept.pattern);
        if (matches) {
          const current = tags.get(concept.name) || { label: concept.label, count: 0 };
          current.count += matches.length;
          tags.set(concept.name, current);
        }
      });
    });
    
    return Array.from(tags.entries())
      .map(([name, data]) => ({ name, ...data }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 15);
  };

  const tags = extractTags();
  
  // Year distribution
  const yearStats = results.reduce((acc, r) => {
    const decade = Math.floor(r.year / 10) * 10;
    acc[decade] = (acc[decade] || 0) + 1;
    return acc;
  }, {});

  return (
    <aside className="sidebar-right">
      <h2>Filter by AI Tags</h2>
      
      {tags.length > 0 && (
        <div className="filter-section">
          <div className="ai-tags-list">
            {tags.map(tag => (
              <button
                key={tag.name}
                className="ai-tag-link"
                onClick={() => onSelectQuery && onSelectQuery(tag.label.toLowerCase())}
                title={`Search for ${tag.label}`}
              >
                {tag.label}
                <span className="tag-count">{tag.count}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="filter-section">
        <h3 className="filter-heading">Related Queries</h3>
        <div className="related-queries">
          {['public policy of india','equality before law','protection of life and liberty','separation of powers','judicial review'].map(q => (
            <button
              key={q}
              className="related-link"
              onClick={() => onSelectQuery && onSelectQuery(q)}
              title={`Search: ${q}`}
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {Object.keys(yearStats).length > 0 && (
        <div className="filter-section">
          <h3 className="filter-heading">Results by Decade</h3>
          <div className="decade-stats">
            {Object.entries(yearStats)
              .sort((a, b) => Number(b[0]) - Number(a[0]))
              .map(([decade, count]) => (
                <div key={decade} className="decade-row">
                  <span>{decade}s</span>
                  <span className="decade-count">{count}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      <div className="filter-section">
        <h3 className="filter-heading">Total Results</h3>
        <div className="total-count">{total.toLocaleString()} judgments</div>
      </div>
    </aside>
  );
}
