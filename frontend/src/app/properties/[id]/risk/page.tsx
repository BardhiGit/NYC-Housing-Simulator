"use client";

import { use, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { financialApi } from "@/lib/api/financial";
import { MonteCarloHistogram } from "@/components/charts/MonteCarloHistogram";
import { TornadoChart } from "@/components/charts/TornadoChart";
import { Button } from "@/components/ui/button";
import { formatPct, formatCurrency } from "@/lib/utils/format";
import { Play, Info } from "lucide-react";

export default function RiskPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [runMC, setRunMC] = useState(false);
  const [runTornado, setRunTornado] = useState(false);

  const { data: mc, isPending: mcPending } = useQuery({
    queryKey: ["monte_carlo", id],
    queryFn: () => financialApi.simulate(id, 2000),
    enabled: runMC,
  });

  const { data: tornado, isPending: tornadoPending } = useQuery({
    queryKey: ["sensitivity", id],
    queryFn: () => financialApi.sensitivity(id, "coc_return"),
    enabled: runTornado,
  });

  return (
    <div className="max-w-5xl space-y-8">
      <div>
        <h2 className="text-lg font-bold text-white mb-1">Risk Analysis</h2>
        <p className="text-sm text-gray-500">Quantify uncertainty and identify the biggest drivers of return.</p>
      </div>

      {/* MC section */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-base font-semibold text-gray-100">Monte Carlo Simulation</h3>
            <p className="text-xs text-gray-500 mt-0.5">2,000 random scenarios varying vacancy, rents, expenses, and exit cap rate</p>
          </div>
          {!runMC && (
            <Button onClick={() => setRunMC(true)}>
              <Play size={13} /> Run Simulation
            </Button>
          )}
        </div>

        {runMC && mcPending && (
          <div className="card flex items-center justify-center h-40 gap-3 text-gray-500">
            <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            Running 2,000 scenarios…
          </div>
        )}

        {mc && <MonteCarloHistogram results={mc} />}

        {mc && (
          <div className="grid md:grid-cols-3 gap-4 mt-4">
            {[
              {
                title: "Bear Case (P10)",
                data: mc.worst_case,
                bg: "bg-red-500/5 border-red-500/20",
                color: "text-red-400",
              },
              {
                title: "Median (P50)",
                data: mc.median_case,
                bg: "bg-gray-900 border-gray-700",
                color: "text-indigo-400",
              },
              {
                title: "Bull Case (P90)",
                data: mc.best_case,
                bg: "bg-emerald-500/5 border-emerald-500/20",
                color: "text-emerald-400",
              },
            ].map(({ title, data, bg, color }) => (
              <div key={title} className={`rounded-xl border p-4 ${bg}`}>
                <div className={`text-sm font-semibold mb-3 ${color}`}>{title}</div>
                {[
                  { label: "IRR",        value: formatPct(data.irr) },
                  { label: "CoC Yr1",    value: formatPct(data.coc_yr1) },
                  { label: "DSCR Yr1",   value: `${(data.dscr_yr1 ?? 0).toFixed(2)}×` },
                  { label: "Exit Equity",value: formatCurrency(data.exit_equity) },
                ].map(({ label, value }) => (
                  <div key={label} className="flex items-center justify-between py-1 border-b border-gray-800/50">
                    <span className="text-xs text-gray-500">{label}</span>
                    <span className="text-sm font-bold mono text-gray-200">{value}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Sensitivity */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-base font-semibold text-gray-100">Sensitivity Analysis</h3>
            <p className="text-xs text-gray-500 mt-0.5">Which assumptions have the biggest impact on cash-on-cash return?</p>
          </div>
          {!runTornado && (
            <Button variant="secondary" onClick={() => setRunTornado(true)}>
              <Play size={13} /> Run Sensitivity
            </Button>
          )}
        </div>

        {runTornado && tornadoPending && (
          <div className="card flex items-center justify-center h-32 gap-3 text-gray-500">
            <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            Calculating sensitivity…
          </div>
        )}

        {tornado && <TornadoChart data={tornado} />}

        {!tornado && !runTornado && (
          <div className="card border-dashed flex items-center gap-3 text-gray-600 text-sm">
            <Info size={14} />
            Run sensitivity to see which variables have the most impact on your return.
          </div>
        )}
      </section>

      {/* Educational disclaimer */}
      <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4">
        <p className="text-xs text-blue-300 font-medium mb-1">About This Analysis</p>
        <p className="text-xs text-gray-400 leading-relaxed">
          Monte Carlo uses truncated normal distributions for vacancy, rent growth, expense growth, and exit cap rate.
          2,000 iterations takes ~5 seconds. 10,000 iterations is available via the API for higher precision.
          This is an educational model — distributions are parameterized from historical NYC data but are not guaranteed to predict future outcomes.
        </p>
      </div>
    </div>
  );
}
