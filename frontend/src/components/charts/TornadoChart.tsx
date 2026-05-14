"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";
import type { TornadoChartData } from "@/lib/types/financial";
import { formatPct } from "@/lib/utils/format";

export function TornadoChart({ data }: { data: TornadoChartData }) {
  // Transform for horizontal bar: each variable has low and high deviation from base
  const base = data.base_value;
  const chartData = data.variables.slice(0, 8).map((v) => ({
    name: v.display_name.replace(/ /g, "\n"),
    low: Math.round((v.low_metric - base) * 10000) / 100,    // as pct points
    high: Math.round((v.high_metric - base) * 10000) / 100,
    swing: v.swing,
    direction: v.direction,
  }));

  const label = data.target_metric === "coc_return" ? "CoC Return" : data.target_metric.toUpperCase();

  return (
    <div className="card">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-100">Sensitivity Analysis — {label}</h3>
        <p className="text-xs text-gray-500 mt-0.5">Impact of ±20% change in each assumption (base: {formatPct(base)})</p>
      </div>
      <div className="space-y-2">
        {data.variables.slice(0, 8).map((v, i) => {
          const maxSwing = data.variables[0]?.swing ?? 1;
          const lowPct = ((base - v.low_metric) / maxSwing) * 50;
          const highPct = ((v.high_metric - base) / maxSwing) * 50;
          return (
            <div key={v.variable} className="flex items-center gap-2">
              <div className="w-28 text-right text-xs text-gray-400 shrink-0 truncate">{v.display_name}</div>
              <div className="flex-1 flex items-center gap-0.5" style={{ height: 20 }}>
                {/* Left bar (pessimistic) */}
                <div className="flex justify-end" style={{ width: "50%" }}>
                  <div
                    className="h-4 bg-red-500/70 rounded-l"
                    style={{ width: `${Math.max(2, lowPct)}%` }}
                  />
                </div>
                {/* Center line */}
                <div className="w-px h-4 bg-gray-600" />
                {/* Right bar (optimistic) */}
                <div style={{ width: "50%" }}>
                  <div
                    className="h-4 bg-emerald-500/70 rounded-r"
                    style={{ width: `${Math.max(2, highPct)}%` }}
                  />
                </div>
              </div>
              <div className="w-14 text-xs text-gray-500 mono shrink-0">
                ±{formatPct(v.swing / 2)}
              </div>
            </div>
          );
        })}
        <div className="flex items-center gap-2 mt-2 pt-2 border-t border-gray-800">
          <div className="w-28" />
          <div className="flex-1 flex justify-between text-[10px] text-gray-600">
            <span>← Pessimistic</span>
            <span>Optimistic →</span>
          </div>
        </div>
      </div>
    </div>
  );
}
