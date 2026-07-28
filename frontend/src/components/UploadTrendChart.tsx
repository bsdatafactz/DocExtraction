import { useState } from "react";
import type { DailyCount } from "../types";

interface Props {
  data: DailyCount[];
}

const WIDTH = 640;
const HEIGHT = 180;
const PAD_LEFT = 32;
const PAD_BOTTOM = 20;
const PAD_TOP = 12;

export function UploadTrendChart({ data }: Props) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (data.length === 0) return null;

  const max = Math.max(1, ...data.map((d) => d.count));
  const plotWidth = WIDTH - PAD_LEFT - 8;
  const plotHeight = HEIGHT - PAD_TOP - PAD_BOTTOM;
  const stepX = plotWidth / Math.max(1, data.length - 1);

  const points = data.map((d, i) => ({
    x: PAD_LEFT + i * stepX,
    y: PAD_TOP + plotHeight - (d.count / max) * plotHeight,
    d,
  }));

  const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  // Sparse axis labels — every ~6th day, never every point.
  const labelEvery = Math.max(1, Math.ceil(data.length / 6));

  return (
    <div className="viz-root chart-card">
      <div className="chart-card-title">Daily Upload Trends</div>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label="Daily upload trends over the last 30 days"
        onMouseLeave={() => setHoverIndex(null)}
      >
        {[0, 0.5, 1].map((frac) => (
          <line
            key={frac}
            className="chart-gridline"
            x1={PAD_LEFT}
            x2={WIDTH - 8}
            y1={PAD_TOP + plotHeight * (1 - frac)}
            y2={PAD_TOP + plotHeight * (1 - frac)}
          />
        ))}
        <text x={4} y={PAD_TOP + 4} className="chart-axis-label">
          {max}
        </text>
        <text x={4} y={PAD_TOP + plotHeight + 4} className="chart-axis-label">
          0
        </text>

        <path d={pathD} className="chart-line" fill="none" />

        {points.map((p, i) => (
          <g key={i}>
            {i % labelEvery === 0 && (
              <text x={p.x} y={HEIGHT - 4} className="chart-axis-label" textAnchor="middle">
                {p.d.date.slice(5)}
              </text>
            )}
            <circle
              cx={p.x}
              cy={p.y}
              r={hoverIndex === i ? 4 : 2.5}
              className="chart-point"
              onMouseEnter={() => setHoverIndex(i)}
            />
            <rect
              x={p.x - stepX / 2}
              y={PAD_TOP}
              width={stepX}
              height={plotHeight}
              fill="transparent"
              onMouseEnter={() => setHoverIndex(i)}
            />
          </g>
        ))}

        {hoverIndex != null && (
          <g>
            <line
              x1={points[hoverIndex].x}
              x2={points[hoverIndex].x}
              y1={PAD_TOP}
              y2={PAD_TOP + plotHeight}
              className="chart-crosshair"
            />
          </g>
        )}
      </svg>
      {hoverIndex != null && (
        <div className="chart-tooltip">
          {points[hoverIndex].d.date}: <strong>{points[hoverIndex].d.count}</strong> upload
          {points[hoverIndex].d.count === 1 ? "" : "s"}
        </div>
      )}
    </div>
  );
}
