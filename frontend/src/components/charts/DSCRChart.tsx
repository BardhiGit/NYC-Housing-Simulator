"use client";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend,
} from "recharts";
import type { YearlyProjection } from "@/lib/types/financial";

export function DSCRChart({ years }: { years: YearlyProjection[] }) {
  const data = years.map((y) => ({
    year: `Y${y.year}`,
    dscr: parseFloat(y.dscr.toFixed(2)),
  }));

  return (
    <div className="card">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-100">DSCR Over Time</h3>
        <p className="text-xs text-gray-500 mt-0.5">Debt service coverage ratio by year</p>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="year" tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis
            tick={{ fill: "#6b7280", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={40}
            tickFormatter={(v) => `${v}×`}
          />
          <Tooltip
            contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
            formatter={(v) => [`${Number(v ?? 0)}×`, "DSCR"]}
          />
          <ReferenceLine y={1.25} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: "1.25× lender min", position: "right", fill: "#f59e0b", fontSize: 10 }} />
          <ReferenceLine y={1.00} stroke="#ef4444" strokeDasharray="4 2" label={{ value: "1.0× break-even", position: "right", fill: "#ef4444", fontSize: 10 }} />
          <Line
            type="monotone"
            dataKey="dscr"
            name="DSCR"
            stroke="#6366f1"
            strokeWidth={2.5}
            dot={{ r: 3, fill: "#6366f1" }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
