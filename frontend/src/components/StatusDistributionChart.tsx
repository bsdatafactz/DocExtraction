interface Props {
  statusCounts: Record<string, number>;
}

// Fixed order + validated palette (see the dataviz skill's validator run for
// this exact hue set) — green/amber/red, our existing status colors reused
// so a status means the same thing here as it does on every badge.
const CATEGORIES = [
  { key: "approved", label: "Approved", cssVar: "--chart-good" },
  { key: "needs_review", label: "Needs review", cssVar: "--chart-warn" },
  { key: "failed", label: "Failed", cssVar: "--chart-bad" },
];

export function StatusDistributionChart({ statusCounts }: Props) {
  const total = CATEGORIES.reduce((sum, c) => sum + (statusCounts[c.key] ?? 0), 0);
  const max = Math.max(1, ...CATEGORIES.map((c) => statusCounts[c.key] ?? 0));

  return (
    <div className="viz-root chart-card">
      <div className="chart-card-title">Documents by Outcome</div>
      <div className="bar-chart">
        {CATEGORIES.map((c) => {
          const count = statusCounts[c.key] ?? 0;
          const pct = total ? Math.round((count / total) * 100) : 0;
          const widthPct = (count / max) * 100;
          return (
            <div className="bar-row" key={c.key}>
              <span className="bar-label">{c.label}</span>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{ width: `${widthPct}%`, background: `var(${c.cssVar})` }}
                />
              </div>
              <span className="bar-value">
                {count} <span className="bar-value-pct">({pct}%)</span>
              </span>
            </div>
          );
        })}
      </div>
      {total === 0 && <p className="page-subtitle">No processed documents yet.</p>}
    </div>
  );
}
