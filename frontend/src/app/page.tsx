"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Building2, BarChart3, AlertTriangle, TrendingUp, Zap, Shield,
  ArrowRight, CheckCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { financialApi } from "@/lib/api/financial";
import { formatCurrency, formatPct, formatDSCR } from "@/lib/utils/format";
import { dscrColor, capRateColor, cocColor } from "@/lib/utils/metrics";
import type { QuickEstimateResult } from "@/lib/types/financial";

function QuickEstimator() {
  const [form, setForm] = useState({
    purchase_price: 1200000,
    total_monthly_rent: 8000,
    vacancy_rate: 0.05,
    total_annual_expenses: 55000,
    loan_amount: 960000,
    annual_rate: 0.0695,
    term_years: 30,
    closing_costs: 36000,
  });
  const [result, setResult] = useState<QuickEstimateResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleRun() {
    setLoading(true); setError("");
    try {
      const r = await financialApi.quickEstimate(form);
      setResult(r);
    } catch {
      setError("Could not connect to the API. Start the backend server first.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 shadow-2xl">
      <h3 className="text-base font-semibold text-gray-100 mb-4 flex items-center gap-2">
        <Zap size={16} className="text-indigo-400" />
        Quick Deal Estimate
      </h3>
      <div className="grid grid-cols-2 gap-3 mb-4">
        {(
          [
            ["purchase_price", "Purchase Price", "$"],
            ["total_monthly_rent", "Monthly Rent (total)", "$"],
            ["total_annual_expenses", "Annual Expenses", "$"],
            ["loan_amount", "Loan Amount", "$"],
            ["annual_rate", "Interest Rate", undefined],
            ["closing_costs", "Closing Costs", "$"],
          ] as [keyof typeof form, string, string | undefined][]
        ).map(([key, label, prefix]) => (
          <Input
            key={key}
            label={label}
            type="number"
            value={form[key]}
            prefix={prefix}
            onChange={(e) => setForm((f) => ({ ...f, [key]: parseFloat(e.target.value) || 0 }))}
          />
        ))}
      </div>
      <Button className="w-full" loading={loading} onClick={handleRun}>
        Run Analysis
      </Button>
      {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
      {result && (
        <div className="mt-4 grid grid-cols-3 gap-2 pt-4 border-t border-gray-800">
          {[
            { label: "Cap Rate",    value: formatPct(result.cap_rate / 100),   color: capRateColor(result.cap_rate / 100) },
            { label: "DSCR",        value: formatDSCR(result.dscr),             color: dscrColor(result.dscr) },
            { label: "Cash-on-Cash",value: formatPct(result.coc_return / 100),  color: cocColor(result.coc_return / 100) },
            { label: "NOI/yr",      value: formatCurrency(result.noi),          color: "text-gray-200" },
            { label: "Cash Flow",   value: formatCurrency(result.cash_flow),    color: result.cash_flow >= 0 ? "text-emerald-400" : "text-red-400" },
            { label: "Break-Even",  value: `${result.break_even_occupancy.toFixed(1)}%`, color: result.break_even_occupancy < 85 ? "text-emerald-400" : "text-amber-400" },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-gray-800 rounded-lg p-2 text-center">
              <div className={`text-sm font-bold mono ${color}`}>{value}</div>
              <div className="text-[10px] text-gray-500 mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const features = [
  { icon: BarChart3,    title: "Institutional-Grade Metrics",  desc: "NOI, DSCR, Cap Rate, CoC, IRR, NPV — calculated precisely for each unit." },
  { icon: Building2,    title: "Unit-Level Rent Roll",         desc: "RS caps, preferential rents, vacancy by unit, market rent gaps." },
  { icon: AlertTriangle,title: "Monte Carlo Risk Analysis",    desc: "10,000 simulation scenarios. Probability of DSCR failure, negative IRR." },
  { icon: TrendingUp,   title: "30-Year Projection",           desc: "Cash flows, equity, debt amortization, and IRR over your holding period." },
  { icon: Shield,       title: "NYC-Specific Rules",           desc: "HSTPA 2019 rules, RGB orders, preferential rent persistence, RS constraints." },
  { icon: Zap,          title: "Investment Quality Score",     desc: "Deterministic 0–100 score with 8 weighted components and letter grade." },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen" style={{ background: "#0a0d14" }}>
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center">
              <Building2 size={14} className="text-white" />
            </div>
            <span className="text-sm font-bold text-white">StrataView</span>
            <span className="ml-1 text-[10px] bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 px-1.5 py-0.5 rounded">NYC</span>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/login"><Button variant="ghost" size="sm">Sign In</Button></Link>
            <Link href="/register"><Button size="sm">Get Started</Button></Link>
          </div>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-6 pt-20 pb-16">
        <div className="grid lg:grid-cols-2 gap-12 items-start">
          <div>
            <div className="inline-flex items-center gap-1.5 bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 text-xs px-3 py-1.5 rounded-full mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
              Built for NYC multifamily real estate
            </div>
            <h1 className="text-4xl font-bold text-white leading-tight mb-4">
              Model the deal<br />
              <span className="text-indigo-400">before you make it.</span>
            </h1>
            <p className="text-gray-400 text-base leading-relaxed mb-6">
              Institutional-grade financial analysis for NYC multifamily buildings. Unit-level
              rent stabilization modeling, Monte Carlo risk simulation, 30-year projections,
              and an Investment Quality Score — in minutes, not spreadsheets.
            </p>
            <div className="flex flex-wrap gap-2 mb-8">
              {["Rent Stabilization", "HSTPA 2019", "Monte Carlo", "IRR & NPV", "Red Flag Detector"].map((t) => (
                <div key={t} className="flex items-center gap-1 text-xs text-gray-400 bg-gray-800/60 border border-gray-700 px-2.5 py-1 rounded-full">
                  <CheckCircle size={10} className="text-emerald-400" />{t}
                </div>
              ))}
            </div>
            <div className="flex gap-3">
              <Link href="/register"><Button size="lg">Start Free <ArrowRight size={14} /></Button></Link>
              <Link href="/login"><Button variant="outline" size="lg">Sign In</Button></Link>
            </div>
            <div className="mt-6 flex items-center gap-4 text-xs text-gray-600 border-t border-gray-800 pt-5">
              <span>3 demo properties included</span><span>·</span>
              <span>No credit card</span><span>·</span><span>Open source</span>
            </div>
          </div>
          <QuickEstimator />
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-16 border-t border-gray-800/50">
        <div className="text-center mb-10">
          <h2 className="text-2xl font-bold text-white mb-2">Everything you need to underwrite an NYC deal</h2>
          <p className="text-gray-500 text-sm">No more spreadsheets. No more optimistic broker pro formas.</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="card-hover">
              <div className="w-8 h-8 rounded-lg bg-indigo-600/15 border border-indigo-500/20 flex items-center justify-center mb-3">
                <Icon size={15} className="text-indigo-400" />
              </div>
              <h3 className="text-sm font-semibold text-gray-100 mb-1">{title}</h3>
              <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 pb-12">
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle size={18} className="text-amber-400 mt-0.5 flex-none" />
            <div>
              <h3 className="text-sm font-semibold text-amber-300 mb-1">The NYC Reality Check</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                At today&apos;s interest rates, most NYC multifamily buildings bought at market price do not generate positive cash flow.
                StrataView shows you exactly why — where expenses consume your NOI, how rent stabilization caps your upside, and what
                would actually need to change for a deal to work. Designed to reveal the truth, not validate an optimistic pro forma.
              </p>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-gray-800 px-6 py-8 mt-8">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-gray-600">
          <span>© 2025 StrataView — Educational tool. Not legal or investment advice.</span>
          <Link href="/register" className="text-indigo-400 hover:text-indigo-300">Get started →</Link>
        </div>
      </footer>
    </div>
  );
}
