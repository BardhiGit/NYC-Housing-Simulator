"use client";

import Link from "next/link";
import { Building2, MapPin, Calendar, ArrowRight } from "lucide-react";
import { formatCurrency, formatCompact } from "@/lib/utils/format";
import { BOROUGH_LABELS } from "@/lib/types/property";
import type { PropertyResponse } from "@/lib/types/property";
import type { Borough } from "@/lib/types/property";

interface Props { property: PropertyResponse; }

export function PropertyCard({ property: p }: Props) {
  return (
    <Link href={`/properties/${p.id}`} className="block">
      <div className="card-hover group cursor-pointer">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-indigo-600/20 border border-indigo-500/20 flex items-center justify-center flex-none">
              <Building2 size={16} className="text-indigo-400" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-100 leading-tight">
                {p.name || "Unnamed Property"}
              </h3>
              <div className="flex items-center gap-1 mt-0.5 text-xs text-gray-500">
                <MapPin size={10} />
                {BOROUGH_LABELS[p.borough as Borough] ?? p.borough}
              </div>
            </div>
          </div>
          <ArrowRight
            size={14}
            className="text-gray-600 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-all mt-1"
          />
        </div>

        <div className="text-xs text-gray-500 truncate mb-3">{p.address || "No address set"}</div>

        <div className="grid grid-cols-3 gap-2">
          <div className="bg-gray-800/60 rounded-lg px-2 py-2">
            <div className="text-base font-bold mono text-gray-100">{p.num_units}</div>
            <div className="text-[10px] text-gray-500">Units</div>
          </div>
          <div className="bg-gray-800/60 rounded-lg px-2 py-2">
            <div className="text-base font-bold mono text-gray-100">{formatCompact(p.purchase_price)}</div>
            <div className="text-[10px] text-gray-500">Price</div>
          </div>
          <div className="bg-gray-800/60 rounded-lg px-2 py-2">
            <div className="text-base font-bold mono text-gray-100">
              {p.year_built ?? "—"}
            </div>
            <div className="text-[10px] text-gray-500">Built</div>
          </div>
        </div>

        <div className="mt-2 flex items-center gap-1 text-[10px] text-gray-600">
          <Calendar size={9} />
          Added {new Date(p.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
        </div>
      </div>
    </Link>
  );
}
