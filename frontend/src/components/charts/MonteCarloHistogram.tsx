"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from "recharts";
import { formatPct } from "@/lib/utils/format";
import type { MonteCarloResults } from "@/lib/types/financial";

function buildHistogram(data: number[], bins = 30) {
  const sorted = [...data].sort((a, b) => a - b);
  const min = sorted[0];
  const max = sorted[sorted.length - 1];
  const width = (max - min) / bins || 0.01;
  const buckets = Array.from({ length: bins }, (_, i) => ({ x: min + i * width, count: 0 }));
  for (const v of sorted) {
    const idx = Math.min(Math.floor((v - min) / width), bins - 1);
    buckets[idx].count++;
  }
  return buckets.map((b) => ({ x: parseFloat(b.x.toFixed(3)), count: b.count }));
}

export function MonteCarloHistogram({ results }: { results: MonteCarloResults }) {
  const hist = buildHistogram(results.irr_histogram, 25);

  return (
    <div className="card">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-100">IRR Distribution</h3>
        <p className="text-xs text-gray-500 mt-0.5">{results.n_iterations.toLocaleString()} simulated scenarios</p>
      </div>
      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          { label: "10th Pct (Bear)", value: formatPct(results.irr.p10) },
          { label: "Median", value: formatPct(results.irr.p50), highlight: true },
          { label: "90th Pct (Bull)", value: formatPct(results.irr.p90) },
        ].map(({ label, value, highlight }) => (
          <div key={label} className="bg-gray-800/60 rounded-lg px-3 py-2 text-center">
            <div className={`text-lg font-bold mono ${highlight ? "text-indigo-400" : "text-gray-200"}`}>{value}</div>
            <div className="text-[10px] text-gray-500 mt-0.5">{label}</div>
          </div>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={hist} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
          <XAxis dataKey="x" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ fill: "#6b7280", fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis hide />
          <Tooltip
            contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8, fontSize: 11 }}
            formatter={(v) => [Number(v ?? 0), "Scenarios"]}
            labelFormatter={(v) => `IRR: ${(Number(v) * 100).toFixed(1)}%`}
          />
          <Bar dataKey="count" radius={[2, 2, 0, 0]}>
            {hist.map((entry, i) => (
              <Cell key={i} fill={entry.x < 0 ? "#ef4444" : entry.x < 0.05 ? "#f59e0b" : "#10b981"} fillOpacity={0.8} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="grid grid-cols-2 gap-3 mt-4 text-center">
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
          <div className="text-lg font-bold mono text-red-400">{(results.p_negative_cashflow_yr1 * 100).toFixed(0)}%</div>
          <div className="text-[10px] text-gray-500">P(Negative CF Year 1)</div>
        </div>
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
          <div className="text-lg font-bold mono text-red-400">{(results.p_dscr_below_1 * 100).toFixed(0)}%</div>
          <div className="text-[10px] text-gray-500">P(DSCR &lt; 1.0×)</div>
        </div>
      </div>
    </div>
  );
}
