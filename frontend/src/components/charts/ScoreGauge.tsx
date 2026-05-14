"use client";

import { scoreGaugeColor, gradeColor } from "@/lib/utils/metrics";
import type { InvestmentScore } from "@/lib/types/financial";

function ArcGauge({ score }: { score: number }) {
  const size = 160;
  const cx = size / 2;
  const cy = size / 2 + 10;
  const r = 60;
  const startAngle = -210;
  const sweep = 240;
  const frac = Math.min(1, Math.max(0, score / 100));
  const valueSweep = frac * sweep;

  function polar(cx: number, cy: number, r: number, angleDeg: number) {
    const rad = (angleDeg * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  }

  function arc(cx: number, cy: number, r: number, startDeg: number, endDeg: number) {
    const s = polar(cx, cy, r, startDeg);
    const e = polar(cx, cy, r, endDeg);
    const large = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`;
  }

  const trackPath = arc(cx, cy, r, startAngle, startAngle + sweep);
  const valuePath = arc(cx, cy, r, startAngle, startAngle + valueSweep);
  const tip = polar(cx, cy, r, startAngle + valueSweep);
  const color = scoreGaugeColor(score);

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Track */}
      <path d={trackPath} fill="none" stroke="#1f2937" strokeWidth={12} strokeLinecap="round" />
      {/* Value */}
      <path d={valuePath} fill="none" stroke={color} strokeWidth={12} strokeLinecap="round" />
      {/* Tip dot */}
      <circle cx={tip.x} cy={tip.y} r={7} fill={color} />
      {/* Zone labels */}
      <text x={cx - 44} y={cy + 36} fill="#ef4444" fontSize={9} textAnchor="middle">Poor</text>
      <text x={cx}       y={cy + 46} fill="#f59e0b" fontSize={9} textAnchor="middle">OK</text>
      <text x={cx + 44}  y={cy + 36} fill="#10b981" fontSize={9} textAnchor="middle">Strong</text>
    </svg>
  );
}

export function ScoreGauge({ score }: { score: InvestmentScore }) {
  const gradeClr = gradeColor(score.letter_grade);

  return (
    <div className="card flex flex-col items-center">
      <h3 className="text-sm font-semibold text-gray-100 self-start mb-3">Investment Quality Score</h3>
      <ArcGauge score={score.total} />
      <div className="text-center -mt-6">
        <div className="text-4xl font-bold mono text-white">{score.total.toFixed(0)}</div>
        <div className={`text-3xl font-bold ${gradeClr}`}>Grade {score.letter_grade}</div>
        <p className="text-xs text-gray-400 mt-2 max-w-[200px] text-center">{score.interpretation}</p>
      </div>
      <div className="w-full mt-4 space-y-2">
        {score.components.filter((c) => c.max_score > 0).map((c) => (
          <div key={c.name}>
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-xs text-gray-500">{c.display_name}</span>
              <span className="text-xs text-gray-300 mono">{c.score.toFixed(0)}/{c.max_score}</span>
            </div>
            <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${Math.max(0, (c.score / c.max_score) * 100)}%`,
                  background: c.score / c.max_score >= 0.75 ? "#10b981" : c.score / c.max_score >= 0.4 ? "#f59e0b" : "#ef4444",
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
