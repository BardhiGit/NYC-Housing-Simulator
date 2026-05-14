"use client";

import {
  ComposedChart, Line, Area, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from "recharts";
import type { YearlyProjection } from "@/lib/types/financial";
import { formatCompact } from "@/lib/utils/format";

interface Props { years: YearlyProjection[]; }

const fmt = (v: number) => formatCompact(v);

export function CashFlowChart({ years }: Props) {
  const data = years.map((y) => ({
    year: `Y${y.year}`,
    noi: Math.round(y.noi),
    debt_service: -Math.round(y.debt_service),
    cash_flow: Math.round(y.cash_flow),
    property_value: Math.round(y.property_value / 1000) * 1000,
  }));

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-100">30-Year Cash Flow Projection</h3>
          <p className="text-xs text-gray-500 mt-0.5">NOI, debt service, and annual cash flow</p>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="year" tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tickFormatter={fmt} tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} width={60} />
          <Tooltip
            contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#d1d5db" }}
            formatter={(v, name) => [formatCompact(Number(v ?? 0)), String(name)]}
          />
          <Legend iconSize={10} wrapperStyle={{ fontSize: 11, color: "#9ca3af" }} />
          <ReferenceLine y={0} stroke="#374151" />
          <Area dataKey="noi" name="NOI" fill="#6366f1" fillOpacity={0.15} stroke="#6366f1" strokeWidth={2} dot={false} />
          <Bar dataKey="cash_flow" name="Cash Flow" fill="#10b981" fillOpacity={0.8} radius={[3, 3, 0, 0]} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
