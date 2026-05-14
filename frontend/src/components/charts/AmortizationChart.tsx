"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { AnnualAmortizationSummary } from "@/lib/types/financial";
import { formatCompact } from "@/lib/utils/format";

export function AmortizationChart({ data }: { data: AnnualAmortizationSummary[] }) {
  const chartData = data.map((d) => ({
    year: `Y${d.year}`,
    Interest: Math.round(d.total_interest),
    Principal: Math.round(d.total_principal),
    Balance: Math.round(d.year_end_balance),
  }));

  return (
    <div className="card">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-100">Amortization: Principal vs. Interest</h3>
        <p className="text-xs text-gray-500 mt-0.5">Annual P&I split and remaining loan balance</p>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
          <defs>
            <linearGradient id="balGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
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
          <Area dataKey="Interest" name="Interest" stackId="1" fill="#ef4444" fillOpacity={0.6} stroke="#ef4444" strokeWidth={0} dot={false} />
          <Area dataKey="Principal" name="Principal" stackId="1" fill="#10b981" fillOpacity={0.6} stroke="#10b981" strokeWidth={0} dot={false} />
          <Area dataKey="Balance" name="Loan Balance" fill="url(#balGrad)" stroke="#f59e0b" strokeWidth={2} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
