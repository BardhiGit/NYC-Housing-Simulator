"use client";

import { MetricCard } from "./MetricCard";
import {
  formatCurrency, formatPct, formatDSCR, formatCompact,
} from "@/lib/utils/format";
import {
  capRateColor, dscrColor, cocColor, breakEvenColor, cashFlowColor, scoreColor,
} from "@/lib/utils/metrics";
import type { FullFinancialResult } from "@/lib/types/financial";
import type { InvestmentScore } from "@/lib/types/financial";

function toColor(c: string): "green" | "amber" | "red" | "blue" | "default" {
  if (c.includes("emerald") || c.includes("green")) return "green";
  if (c.includes("amber")) return "amber";
  if (c.includes("red")) return "red";
  if (c.includes("indigo")) return "blue";
  return "default";
}

interface KPIGridProps {
  fin: FullFinancialResult;
  score?: InvestmentScore;
}

export function KPIGrid({ fin, score }: KPIGridProps) {
  const { income, operating, debt, returns, break_even } = fin;
  const noi = operating.net_operating_income;
  const cap = returns.cap_rate;
  const dscr = debt?.dscr ?? null;
  const coc = returns.cash_on_cash_return;
  const be = break_even.break_even_occupancy;
  const cf = returns.cash_flow_before_tax;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      <MetricCard
        label="Net Operating Income"
        value={formatCompact(noi)}
        subtitle="Annual NOI"
        color={noi > 0 ? "green" : "red"}
        tooltip="EGI minus all operating expenses. Core profitability metric."
        badge="NOI"
      />
      <MetricCard
        label="Cap Rate"
        value={formatPct(cap)}
        subtitle="Unlevered yield"
        color={toColor(capRateColor(cap))}
        tooltip="NOI / Purchase Price. NYC range: 3.5–6%"
        badge="Cap"
      />
      <MetricCard
        label="DSCR"
        value={dscr != null ? formatDSCR(dscr) : "N/A"}
        subtitle={dscr != null ? (dscr >= 1.25 ? "Lender-safe" : dscr >= 1.0 ? "Tight" : "Below 1.0x!") : "All cash"}
        color={dscr != null ? toColor(dscrColor(dscr)) : "default"}
        tooltip="NOI / Annual Debt Service. Must exceed 1.25x for most lenders."
        badge="DSCR"
      />
      <MetricCard
        label="Cash-on-Cash"
        value={formatPct(coc)}
        subtitle="Year-1 equity return"
        color={toColor(cocColor(coc))}
        tooltip="Annual cash flow / total equity invested."
        badge="CoC"
      />
      <MetricCard
        label="Break-Even Occ."
        value={formatPct(be)}
        subtitle={be < 0.85 ? "Comfortable" : be < 0.95 ? "Tight" : "Risky"}
        color={toColor(breakEvenColor(be))}
        tooltip="Minimum occupancy to cover all costs. Below 85% is healthy."
        badge="B/E"
      />
      {score ? (
        <MetricCard
          label="Investment Score"
          value={`${score.total.toFixed(0)}/100`}
          subtitle={`Grade ${score.letter_grade}`}
          color={toColor(scoreColor(score.total))}
          tooltip="Composite investment quality score (0–100)."
          badge="Score"
        />
      ) : (
        <MetricCard
          label="Cash Flow"
          value={formatCurrency(cf)}
          subtitle="Annual pre-tax"
          color={toColor(cashFlowColor(cf))}
          tooltip="NOI minus annual debt service."
          badge="CF"
        />
      )}
    </div>
  );
}
