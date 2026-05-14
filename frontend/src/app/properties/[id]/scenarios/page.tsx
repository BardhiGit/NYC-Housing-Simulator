"use client";

import { use, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { propertiesApi } from "@/lib/api/properties";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatPct, formatCurrency, formatDSCR, formatMultiple } from "@/lib/utils/format";
import { dscrColor, capRateColor, cocColor } from "@/lib/utils/metrics";
import { clsx } from "clsx";
import { Plus, Play, Loader2 } from "lucide-react";

const presets = [
  { type: "base",        name: "Base Case",    color: "indigo" },
  { type: "optimistic",  name: "Bull Case",    color: "emerald" },
  { type: "pessimistic", name: "Bear Case",    color: "red" },
  { type: "rent_freeze", name: "Rent Freeze",  color: "amber" },
  { type: "high_rates",  name: "Higher Rates", color: "orange" },
];

export default function ScenariosPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const qc = useQueryClient();
  const [running, setRunning] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [results, setResults] = useState<Record<string, any>>({});

  const { data: scenarios = [] } = useQuery({
    queryKey: ["scenarios", id],
    queryFn: () => propertiesApi.listScenarios(id),
  });

  const createMutation = useMutation({
    mutationFn: (type: string) =>
      propertiesApi.createScenario(id, {
        name: presets.find((p) => p.type === type)?.name ?? type,
        type,
        overrides: {},
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenarios", id] }),
  });

  async function runScenario(scenarioId: string) {
    setRunning(scenarioId);
    const result = await propertiesApi.runScenario(id, scenarioId);
    setResults((r) => ({ ...r, [scenarioId]: result }));
    setRunning(null);
  }

  function addAllPresets() {
    const existing = new Set(scenarios.map((s) => s.type));
    presets.forEach(({ type }) => {
      if (!existing.has(type)) createMutation.mutate(type);
    });
  }

  return (
    <div className="max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-white">Scenario Analysis</h2>
          <p className="text-sm text-gray-500 mt-0.5">Compare this deal under different market assumptions</p>
        </div>
        <Button onClick={addAllPresets} loading={createMutation.isPending}>
          <Plus size={14} /> Add All Presets
        </Button>
      </div>

      {scenarios.length === 0 && (
        <div className="card flex flex-col items-center py-12 text-center text-gray-500">
          <p className="text-sm mb-4">No scenarios yet. Add preset scenarios to compare outcomes.</p>
          <Button onClick={addAllPresets}><Plus size={14} /> Add Preset Scenarios</Button>
        </div>
      )}

      <div className="space-y-3">
        {scenarios.map((s) => {
          const r = results[s.id];
          const isRunning = running === s.id;
          const preset = presets.find((p) => p.type === s.type);
          return (
            <div key={s.id} className="card">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={clsx(
                    "px-2.5 py-1 rounded-full text-xs font-semibold",
                    s.type === "base"        && "bg-indigo-600/20 text-indigo-400",
                    s.type === "optimistic"  && "bg-emerald-600/20 text-emerald-400",
                    s.type === "pessimistic" && "bg-red-600/20 text-red-400",
                    s.type === "rent_freeze" && "bg-amber-600/20 text-amber-400",
                    s.type === "high_rates"  && "bg-orange-600/20 text-orange-400",
                    !["base","optimistic","pessimistic","rent_freeze","high_rates"].includes(s.type) && "bg-gray-700 text-gray-300",
                  )}>
                    {s.name}
                  </div>
                  {Object.keys(s.overrides).length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap">
                      {Object.entries(s.overrides).slice(0, 3).map(([k, v]) => (
                        <span key={k} className="text-[10px] bg-gray-800 text-gray-400 border border-gray-700 px-1.5 py-0.5 rounded">
                          {k.replace(/_/g, " ")}: {typeof v === "number" && v < 1 ? formatPct(v) : v}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <Button size="sm" variant="secondary" onClick={() => runScenario(s.id)} loading={isRunning}>
                  {isRunning ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
                  {isRunning ? "Running…" : "Run"}
                </Button>
              </div>

              {r && (
                <div className="grid grid-cols-2 md:grid-cols-6 gap-2 mt-3 pt-3 border-t border-gray-800">
                  {[
                    { label: "Cap Rate",     value: formatPct(r.financials?.returns?.cap_rate),          color: capRateColor(r.financials?.returns?.cap_rate ?? 0) },
                    { label: "DSCR",         value: r.financials?.debt ? formatDSCR(r.financials.debt.dscr) : "N/A", color: r.financials?.debt ? dscrColor(r.financials.debt.dscr) : "text-gray-300" },
                    { label: "CoC",          value: formatPct(r.financials?.returns?.cash_on_cash_return), color: cocColor(r.financials?.returns?.cash_on_cash_return ?? 0) },
                    { label: "IRR",          value: formatPct(r.projection_summary?.irr),               color: "text-gray-200" },
                    { label: "Equity ×",     value: formatMultiple(r.projection_summary?.equity_multiple), color: "text-gray-200" },
                    { label: "Score",        value: `${r.score?.total?.toFixed(0) ?? "—"} (${r.score?.letter_grade ?? "?"})`, color: "text-gray-200" },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-gray-800/60 rounded-lg p-2 text-center">
                      <div className={`text-sm font-bold mono ${color}`}>{value}</div>
                      <div className="text-[10px] text-gray-500 mt-0.5">{label}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
