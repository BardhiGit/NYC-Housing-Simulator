"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { YearlyProjection } from "@/lib/types/financial";
import { formatCompact } from "@/lib/utils/format";

export function EquityBuildupChart({ years }: { years: YearlyProjection[] }) {
  const data = years.map((y) => ({
    year: `Y${y.year}`,
    Equity: Math.round(y.equity),
    "Loan Balance": Math.round(y.loan_balance),
  }));

  return (
    <div className="card">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-100">Equity Buildup</h3>
        <p className="text-xs text-gray-500 mt-0.5">Equity vs. remaining loan balance over time</p>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
          <defs>
            <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#10b981" stopOpacity={0.05} />
            </linearGradient>
            <linearGradient id="loanGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#ef4444" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="year" tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tickFormatter={formatCompact} tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} width={60} />
          <Tooltip
            contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
            formatter={(v, name) => [formatCompact(Number(v ?? 0)), String(name)]}
          />
          <Legend iconSize={10} wrapperStyle={{ fontSize: 11, color: "#9ca3af" }} />
          <Area dataKey="Equity" fill="url(#eqGrad)" stroke="#10b981" strokeWidth={2} dot={false} />
          <Area dataKey="Loan Balance" fill="url(#loanGrad)" stroke="#ef4444" strokeWidth={2} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
