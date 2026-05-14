"use client";

import { useState } from "react";
import { Pencil, Trash2, Plus } from "lucide-react";
import { RentTypeBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatCurrency, formatPct } from "@/lib/utils/format";
import type { UnitResponse } from "@/lib/types/property";

interface Props {
  units: UnitResponse[];
  onAdd: () => void;
  onEdit: (unit: UnitResponse) => void;
  onDelete: (unit: UnitResponse) => void;
}

export function RentRollTable({ units, onAdd, onEdit, onDelete }: Props) {
  const totalGSI = units
    .filter((u) => u.rent_type !== "vacant" && u.rent_type !== "owner_occupied")
    .reduce((sum, u) => sum + u.current_rent * 12, 0);

  const rsCnt = units.filter((u) => u.rent_type === "stabilized").length;
  const fmCnt = units.filter((u) => u.rent_type === "free_market").length;
  const vacCnt = units.filter((u) => u.rent_type === "vacant").length;
  const rentable = rsCnt + fmCnt;
  const rsPct = rentable > 0 ? rsCnt / rentable : 0;

  return (
    <div>
      {/* Summary bar */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        {[
          { label: "Annual GSI", value: formatCurrency(totalGSI), sub: "at 100% occupancy" },
          { label: "RS Units", value: rsCnt.toString(), sub: rentable > 0 ? `${formatPct(rsPct)} of rentable` : "—" },
          { label: "FM Units", value: fmCnt.toString(), sub: "free market" },
          { label: "Vacant", value: vacCnt.toString(), sub: "not generating income" },
        ].map(({ label, value, sub }) => (
          <div key={label} className="card">
            <div className="text-xl font-bold mono text-gray-100">{value}</div>
            <div className="text-xs font-medium text-gray-400 mt-0.5">{label}</div>
            <div className="text-[10px] text-gray-600">{sub}</div>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="card !p-0 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
          <h3 className="text-sm font-semibold text-gray-100">Rent Roll</h3>
          <Button size="sm" onClick={onAdd}>
            <Plus size={13} /> Add Unit
          </Button>
        </div>

        {units.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-500">
            <div className="text-sm mb-2">No units added yet</div>
            <Button size="sm" onClick={onAdd}><Plus size={13} /> Add first unit</Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 uppercase tracking-wide border-b border-gray-800">
                  <th className="px-4 py-2 text-left">Unit</th>
                  <th className="px-4 py-2 text-left">Type</th>
                  <th className="px-4 py-2 text-left">Beds</th>
                  <th className="px-4 py-2 text-right">Current Rent</th>
                  <th className="px-4 py-2 text-right">Legal Rent</th>
                  <th className="px-4 py-2 text-right">Market Est.</th>
                  <th className="px-4 py-2 text-right">Annual</th>
                  <th className="px-4 py-2 text-left">Lease Expiry</th>
                  <th className="px-4 py-2 text-right">Vacancy</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {units.map((u) => {
                  const isVacant = u.rent_type === "vacant" || u.rent_type === "owner_occupied";
                  const marketGap = u.market_rent_est && u.current_rent > 0
                    ? (u.market_rent_est - u.current_rent) / u.market_rent_est
                    : null;
                  return (
                    <tr key={u.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                      <td className="px-4 py-2.5 font-medium text-gray-200">{u.unit_number}</td>
                      <td className="px-4 py-2.5"><RentTypeBadge type={u.rent_type} /></td>
                      <td className="px-4 py-2.5 text-gray-400">{u.bedrooms}BR</td>
                      <td className="px-4 py-2.5 text-right mono text-gray-200">
                        {isVacant ? <span className="text-gray-600">—</span> : formatCurrency(u.current_rent)}
                      </td>
                      <td className="px-4 py-2.5 text-right mono text-gray-400 text-xs">
                        {u.legal_rent ? formatCurrency(u.legal_rent) : "—"}
                      </td>
                      <td className="px-4 py-2.5 text-right">
                        {u.market_rent_est ? (
                          <span className="mono text-gray-400 text-xs">
                            {formatCurrency(u.market_rent_est)}
                            {marketGap !== null && (
                              <span className="ml-1 text-amber-500">
                                (+{formatPct(marketGap, 0)})
                              </span>
                            )}
                          </span>
                        ) : "—"}
                      </td>
                      <td className="px-4 py-2.5 text-right mono text-gray-300">
                        {isVacant ? "—" : formatCurrency(u.current_rent * 12)}
                      </td>
                      <td className="px-4 py-2.5 text-gray-400 text-xs">
                        {u.lease_expiry ?? "—"}
                      </td>
                      <td className="px-4 py-2.5 text-right mono text-gray-400 text-xs">
                        {formatPct(u.vacancy_rate, 0)}
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-1 justify-end">
                          <button onClick={() => onEdit(u)} className="p-1.5 text-gray-600 hover:text-indigo-400 hover:bg-gray-700 rounded transition-colors">
                            <Pencil size={12} />
                          </button>
                          <button onClick={() => onDelete(u)} className="p-1.5 text-gray-600 hover:text-red-400 hover:bg-gray-700 rounded transition-colors">
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="bg-gray-800/30 border-t border-gray-700">
                  <td colSpan={6} className="px-4 py-2 text-xs font-semibold text-gray-400">Totals</td>
                  <td className="px-4 py-2 text-right mono text-sm font-bold text-gray-100">{formatCurrency(totalGSI)}</td>
                  <td colSpan={3} />
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
