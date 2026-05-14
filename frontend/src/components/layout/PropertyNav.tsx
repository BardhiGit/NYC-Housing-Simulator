"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import {
  LayoutGrid, Users, BarChart3, GitBranch, AlertTriangle, FileText, ArrowLeft,
} from "lucide-react";

const tabs = [
  { href: "",           icon: LayoutGrid,   label: "Overview" },
  { href: "/units",     icon: Users,        label: "Rent Roll" },
  { href: "/financials",icon: BarChart3,    label: "Financials" },
  { href: "/scenarios", icon: GitBranch,    label: "Scenarios" },
  { href: "/risk",      icon: AlertTriangle, label: "Risk" },
  { href: "/memo",      icon: FileText,     label: "Memo" },
];

export function PropertyNav({ propertyId, propertyName }: { propertyId: string; propertyName: string }) {
  const pathname = usePathname();
  const base = `/properties/${propertyId}`;

  return (
    <div className="border-b border-gray-800 bg-gray-950/70 backdrop-blur sticky top-0 z-20">
      <div className="px-6 pt-3">
        <div className="flex items-center gap-2 mb-3">
          <Link href="/dashboard" className="text-gray-500 hover:text-gray-300 transition-colors">
            <ArrowLeft size={14} />
          </Link>
          <span className="text-gray-600 text-sm">/</span>
          <span className="text-gray-300 text-sm font-medium truncate max-w-xs">{propertyName}</span>
        </div>
        <div className="flex gap-0.5">
          {tabs.map(({ href, icon: Icon, label }) => {
            const to = `${base}${href}`;
            const active = href === "" ? pathname === base : pathname.startsWith(to);
            return (
              <Link
                key={to}
                href={to}
                className={clsx(
                  "flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-t-lg transition-colors border-b-2",
                  active
                    ? "text-indigo-400 border-indigo-500 bg-indigo-500/5"
                    : "text-gray-500 border-transparent hover:text-gray-300 hover:bg-gray-800/50",
                )}
              >
                <Icon size={13} />
                {label}
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
