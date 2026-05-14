"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowRight, Building2, MapPin, Calendar } from "lucide-react";
import { propertiesApi } from "@/lib/api/properties";
import { financialApi } from "@/lib/api/financial";
import { formatCurrency, formatPct, formatDSCR, formatCompact } from "@/lib/utils/format";
import { dscrColor, capRateColor, cocColor } from "@/lib/utils/metrics";
import { RentTypeBadge } from "@/components/ui/badge";
import { BOROUGH_LABELS } from "@/lib/types/property";
import type { Borough } from "@/lib/types/property";

export default function PropertyOverviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const { data: property } = useQuery({ queryKey: ["property", id], queryFn: () => propertiesApi.get(id) });
  const { data: fin } = useQuery({ queryKey: ["financials", id], queryFn: () => financialApi.calculate(id), enabled: !!property });

  const quickLinks = [
    { href: `/properties/${id}/units`,      label: "Manage Rent Roll →",  sub: `${property?.units?.length ?? 0} units` },
    { href: `/properties/${id}/financials`, label: "View Full Dashboard →", sub: "NOI, DSCR, charts" },
    { href: `/properties/${id}/risk`,       label: "Run Risk Analysis →",  sub: "Monte Carlo, tornado" },
    { href: `/properties/${id}/memo`,       label: "Generate Deal Memo →", sub: "Strengths, risks, offer" },
  ];

  return (
    <div className="max-w-4xl space-y-6">
      {/* Property header */}
      <div className="card">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-600/15 border border-indigo-500/20 flex items-center justify-center flex-none">
            <Building2 size={20} className="text-indigo-400" />
          </div>
          <div className="flex-1">
            <h1 className="text-lg font-bold text-white">{property?.name || "Property Overview"}</h1>
            {property?.address && (
              <div className="flex items-center gap-1.5 text-sm text-gray-400 mt-0.5">
                <MapPin size={12} />
                {property.address}
              </div>
            )}
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              <span>{BOROUGH_LABELS[property?.borough as Borough] ?? property?.borough}</span>
              <span>·</span>
              <span>{property?.num_units} units</span>
              {property?.year_built && <><span>·</span><span>Built {property.year_built}</span></>}
              <span>·</span>
              <span>{formatCompact(property?.purchase_price ?? 0)}</span>
            </div>
          </div>
        </div>

        {/* Unit mix */}
        {property?.units && property.units.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {Array.from(new Set(property.units.map((u) => u.rent_type))).map((t) => {
              const cnt = property.units.filter((u) => u.rent_type === t).length;
              return (
                <div key={t} className="flex items-center gap-1.5 bg-gray-800/60 rounded-full px-2.5 py-1">
                  <RentTypeBadge type={t as "stabilized" | "free_market" | "vacant" | "owner_occupied"} />
                  <span className="text-xs text-gray-400">{cnt}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Key metrics */}
      {fin && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Cap Rate",     value: formatPct(fin.returns.cap_rate),                  color: capRateColor(fin.returns.cap_rate) },
            { label: "DSCR",         value: fin.debt ? formatDSCR(fin.debt.dscr) : "All-cash", color: fin.debt ? dscrColor(fin.debt.dscr) : "text-gray-300" },
            { label: "Cash-on-Cash", value: formatPct(fin.returns.cash_on_cash_return),        color: cocColor(fin.returns.cash_on_cash_return) },
            { label: "Annual NOI",   value: formatCompact(fin.operating.net_operating_income), color: "text-gray-100" },
          ].map(({ label, value, color }) => (
            <div key={label} className="card text-center">
              <div className={`text-xl font-bold mono ${color}`}>{value}</div>
              <div className="text-xs text-gray-500 mt-1">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Quick nav */}
      <div className="grid md:grid-cols-2 gap-3">
        {quickLinks.map(({ href, label, sub }) => (
          <Link key={href} href={href}>
            <div className="card-hover flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-indigo-400">{label}</div>
                <div className="text-xs text-gray-500 mt-0.5">{sub}</div>
              </div>
              <ArrowRight size={14} className="text-gray-600" />
            </div>
          </Link>
        ))}
      </div>

      {/* Assumptions */}
      {property?.assumptions && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-200 mb-3">Projection Assumptions</h3>
          <div className="grid grid-cols-3 md:grid-cols-5 gap-3 text-center">
            {[
              { label: "Hold Period", value: `${property.assumptions.holding_period}yr` },
              { label: "FM Rent Growth", value: formatPct(property.assumptions.fm_rent_growth_rate) },
              { label: "RS Rent Growth", value: formatPct(property.assumptions.rs_rent_growth_rate) },
              { label: "Exit Cap Rate", value: formatPct(property.assumptions.exit_cap_rate) },
              { label: "Vacancy Rate", value: formatPct(property.assumptions.general_vacancy_rate) },
            ].map(({ label, value }) => (
              <div key={label}>
                <div className="text-sm font-bold mono text-gray-200">{value}</div>
                <div className="text-[10px] text-gray-600 mt-0.5">{label}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
