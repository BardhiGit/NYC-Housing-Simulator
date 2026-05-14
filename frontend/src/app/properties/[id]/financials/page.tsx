"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { financialApi } from "@/lib/api/financial";
import { KPIGrid } from "@/components/financial/KPIGrid";
import { RedFlagList } from "@/components/financial/RedFlagList";
import { CashFlowChart } from "@/components/charts/CashFlowChart";
import { AmortizationChart } from "@/components/charts/AmortizationChart";
import { ExpenseDonutChart } from "@/components/charts/ExpenseDonutChart";
import { DSCRChart } from "@/components/charts/DSCRChart";
import { ScoreGauge } from "@/components/charts/ScoreGauge";
import { EquityBuildupChart } from "@/components/charts/EquityBuildupChart";
import { formatCurrency, formatPct, formatDSCR, formatCompact, formatMultiple } from "@/lib/utils/format";

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-3">
      <h2 className="text-base font-semibold text-gray-100">{title}</h2>
      {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
    </div>
  );
}

export default function FinancialsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const { data: fin, isPending: finPending, error: finError } = useQuery({
    queryKey: ["financials", id],
    queryFn: () => financialApi.calculate(id),
  });
  const { data: projection } = useQuery({
    queryKey: ["projection", id],
    queryFn: () => financialApi.project(id),
    enabled: !!fin,
  });
  const { data: amortization } = useQuery({
    queryKey: ["amortization", id],
    queryFn: () => financialApi.amortize(id),
    enabled: !!fin?.debt,
  });
  const { data: score } = useQuery({
    queryKey: ["score", id],
    queryFn: () => financialApi.score(id),
    enabled: !!fin,
  });
  const { data: flagsData } = useQuery({
    queryKey: ["flags", id],
    queryFn: () => financialApi.flags(id),
    enabled: !!fin,
  });

  if (finPending) {
    return (
      <div className="max-w-5xl space-y-4">
        <div className="grid grid-cols-6 gap-3">{[1,2,3,4,5,6].map((i) => <div key={i} className="card h-20 animate-pulse bg-gray-900/50" />)}</div>
        <div className="grid grid-cols-2 gap-4">{[1,2].map((i) => <div key={i} className="card h-64 animate-pulse bg-gray-900/50" />)}</div>
      </div>
    );
  }

  if (finError) {
    return (
      <div className="max-w-5xl">
        <div className="card border-red-500/20 bg-red-500/5 text-red-400">
          <p className="text-sm font-medium">Could not calculate financials</p>
          <p className="text-xs mt-1 text-red-300">Add at least one unit and save your loan details, then try again.</p>
        </div>
      </div>
    );
  }

  if (!fin) return null;

  return (
    <div className="max-w-5xl space-y-8">
      {/* KPI Strip */}
      <section>
        <SectionHeader title="Key Performance Indicators" subtitle="Year-1 analysis based on current rent roll and expenses" />
        <KPIGrid fin={fin} score={score} />
      </section>

      {/* Income waterfall */}
      <section>
        <SectionHeader title="Income & Expense Structure" />
        <div className="grid md:grid-cols-2 gap-4">
          {/* Income statement card */}
          <div className="card space-y-0">
            <h3 className="text-sm font-semibold text-gray-100 mb-4">Annual Income Statement</h3>
            {[
              { label: "Gross Scheduled Income",     value: fin.income.gross_scheduled_income,     indent: 0, bold: false },
              { label: "Vacancy Loss",               value: -fin.income.vacancy_loss,              indent: 1, bold: false, neg: true },
              { label: "Other Income",               value: fin.income.other_income,               indent: 1, bold: false },
              { label: "Effective Gross Income",     value: fin.income.total_income,               indent: 0, bold: true },
              { label: "Total Operating Expenses",   value: -fin.operating.total_operating_expenses, indent: 1, bold: false, neg: true },
              { label: "Net Operating Income",       value: fin.operating.net_operating_income,    indent: 0, bold: true, color: fin.operating.net_operating_income > 0 ? "text-emerald-400" : "text-red-400" },
              ...(fin.debt ? [
                { label: "Annual Debt Service",      value: -fin.debt.annual_debt_service,         indent: 1, bold: false, neg: true },
                { label: "Cash Flow Before Tax",     value: fin.returns.cash_flow_before_tax,      indent: 0, bold: true, color: fin.returns.cash_flow_before_tax >= 0 ? "text-emerald-400" : "text-red-400" },
              ] : []),
            ].map(({ label, value, indent, bold, color }) => (
              <div key={label} className={`flex items-center justify-between py-1.5 border-b border-gray-800/50 ${bold ? "mt-1" : ""}`}>
                <span className={`text-xs ${indent ? "pl-3 text-gray-500" : "text-gray-300 font-medium"}`}>{label}</span>
                <span className={`text-xs mono font-semibold ${color ?? (value < 0 ? "text-red-400" : "text-gray-200")}`}>
                  {formatCurrency(Math.abs(value))}
                </span>
              </div>
            ))}
          </div>

          <ExpenseDonutChart expensesByCategory={fin.operating.expense_by_category} />
        </div>
      </section>

      {/* Ratios */}
      <section>
        <SectionHeader title="Financial Ratios & Benchmarks" />
        <div className="card">
          <div className="grid md:grid-cols-3 gap-0 divide-y md:divide-y-0 md:divide-x divide-gray-800">
            {[
              {
                group: "Returns",
                items: [
                  { label: "Cap Rate",            value: formatPct(fin.returns.cap_rate),                       benchmark: "NYC: 3.5–6%", good: fin.returns.cap_rate >= 0.045 },
                  { label: "Cash-on-Cash",        value: formatPct(fin.returns.cash_on_cash_return),             benchmark: "Target: 5–8%", good: fin.returns.cash_on_cash_return >= 0.05 },
                  { label: "Expense Ratio",       value: formatPct(fin.operating.expense_ratio),               benchmark: "NYC: 35–55%", good: fin.operating.expense_ratio <= 0.55 },
                ],
              },
              {
                group: "Debt Coverage",
                items: [
                  { label: "DSCR",                value: fin.debt ? formatDSCR(fin.debt.dscr) : "All-cash",    benchmark: "Lender min: 1.25×", good: !fin.debt || fin.debt.dscr >= 1.25 },
                  { label: "Break-even Occ.",     value: formatPct(fin.break_even.break_even_occupancy),        benchmark: "Safe: < 85%", good: fin.break_even.break_even_occupancy < 0.85 },
                  { label: "LTV",                 value: fin.debt ? formatPct(fin.debt.loan_to_value) : "0%",  benchmark: "Max: 80%", good: !fin.debt || fin.debt.loan_to_value <= 0.80 },
                ],
              },
              {
                group: "Valuation",
                items: [
                  { label: "Price per Unit",      value: formatCurrency(fin.valuation.price_per_unit),         benchmark: "" },
                  { label: "Implied Value",       value: formatCompact(fin.valuation.implied_value_at_cap),    benchmark: "At current cap rate" },
                  { label: "RS %",                value: formatPct(fin.rent_roll.rs_percentage, 0),            benchmark: "Higher = more constrained", good: fin.rent_roll.rs_percentage < 0.5 },
                ],
              },
            ].map(({ group, items }) => (
              <div key={group} className="px-4 py-2">
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{group}</div>
                <div className="space-y-2">
                  {items.map(({ label, value, benchmark, good }) => (
                    <div key={label} className="flex items-start justify-between gap-2">
                      <div>
                        <div className="text-xs text-gray-400">{label}</div>
                        {benchmark && <div className="text-[10px] text-gray-600">{benchmark}</div>}
                      </div>
                      <div className={`text-sm font-bold mono ${good === true ? "text-emerald-400" : good === false ? "text-red-400" : "text-gray-200"}`}>
                        {value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Projection charts */}
      {projection && (
        <section>
          <SectionHeader
            title={`${projection.holding_period}-Year Projection`}
            subtitle={`IRR: ${formatPct(projection.irr)} · Equity Multiple: ${formatMultiple(projection.equity_multiple)} · Exit Proceeds: ${formatCompact(projection.exit_net_proceeds)}`}
          />
          <div className="grid md:grid-cols-2 gap-4">
            <CashFlowChart years={projection.years} />
            <EquityBuildupChart years={projection.years} />
          </div>
          {fin.debt && <div className="mt-4"><DSCRChart years={projection.years} /></div>}
        </section>
      )}

      {/* Amortization */}
      {amortization && (
        <section>
          <SectionHeader
            title="Amortization Schedule"
            subtitle={`Monthly payment: ${formatCurrency(amortization.monthly_payment)} · Total interest: ${formatCompact(amortization.total_interest)}`}
          />
          <AmortizationChart data={amortization.annual_summary} />
        </section>
      )}

      {/* Score + Flags */}
      <section>
        <SectionHeader title="Investment Quality Score" subtitle="Deterministic scoring based on 8 financial metrics" />
        <div className="grid md:grid-cols-2 gap-4">
          {score && <ScoreGauge score={score} />}
          <div>
            <h3 className="text-sm font-semibold text-gray-100 mb-3">
              Red Flags {flagsData && <span className="text-gray-500 font-normal">({flagsData.count} found)</span>}
            </h3>
            {flagsData && <RedFlagList flags={flagsData.flags} />}
          </div>
        </div>
      </section>
    </div>
  );
}
