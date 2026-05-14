"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { formatCurrency, formatPct } from "@/lib/utils/format";
import { EXPENSE_LABELS } from "@/lib/types/property";
import type { ExpenseCategory } from "@/lib/types/property";

const COLORS = [
  "#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6",
  "#ec4899","#14b8a6","#f97316","#a855f7","#06b6d4","#84cc16",
];

export function ExpenseDonutChart({ expensesByCategory }: { expensesByCategory: Record<string, number> }) {
  const total = Object.values(expensesByCategory).reduce((a, b) => a + b, 0);
  const data = Object.entries(expensesByCategory)
    .sort((a, b) => b[1] - a[1])
    .map(([key, value]) => ({
      name: EXPENSE_LABELS[key as ExpenseCategory] ?? key,
      value: Math.round(value),
      pct: value / total,
    }));

  return (
    <div className="card">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-100">Expense Breakdown</h3>
        <p className="text-xs text-gray-500 mt-0.5">Total: {formatCurrency(total)}/yr</p>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={90}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
            formatter={(v, name) => [formatCurrency(Number(v ?? 0)), String(name)]}
          />
          <Legend
            iconSize={8}
            iconType="circle"
            wrapperStyle={{ fontSize: 10, color: "#9ca3af" }}
            formatter={(v, entry) => `${v} (${formatPct((entry.payload as { pct?: number })?.pct ?? 0)})`}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
