"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Plus, Building2 } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PropertyCard } from "@/components/property/PropertyCard";
import { Button } from "@/components/ui/button";
import { propertiesApi } from "@/lib/api/properties";

export default function DashboardPage() {
  const { data: properties = [], isPending } = useQuery({
    queryKey: ["properties"],
    queryFn: propertiesApi.list,
  });

  return (
    <AppShell>
      <div className="p-6 max-w-5xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-white">My Properties</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {properties.length} {properties.length === 1 ? "property" : "properties"} in your portfolio
            </p>
          </div>
          <Link href="/properties/new">
            <Button><Plus size={14} /> New Property</Button>
          </Link>
        </div>

        {/* States */}
        {isPending && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card h-40 animate-pulse bg-gray-900/50" />
            ))}
          </div>
        )}

        {!isPending && properties.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-14 h-14 rounded-2xl bg-gray-900 border border-gray-700 flex items-center justify-center mb-4">
              <Building2 size={22} className="text-gray-600" />
            </div>
            <h2 className="text-base font-semibold text-gray-300 mb-1">No properties yet</h2>
            <p className="text-sm text-gray-500 mb-6 max-w-xs">
              Add your first NYC multifamily property to start the financial analysis.
            </p>
            <Link href="/properties/new">
              <Button><Plus size={14} /> Add First Property</Button>
            </Link>
          </div>
        )}

        {!isPending && properties.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {properties.map((p) => (
              <PropertyCard key={p.id} property={p} />
            ))}
            <Link href="/properties/new" className="block">
              <div className="card-hover flex flex-col items-center justify-center h-full min-h-[140px] border-dashed text-gray-600 hover:text-indigo-400 hover:border-indigo-500/40 cursor-pointer">
                <Plus size={20} className="mb-2" />
                <span className="text-sm font-medium">Add Property</span>
              </div>
            </Link>
          </div>
        )}
      </div>
    </AppShell>
  );
}
