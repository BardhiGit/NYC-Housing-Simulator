"use client";

import { clsx } from "clsx";
import { Info } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string;
  subtitle?: string;
  color?: "green" | "amber" | "red" | "blue" | "default";
  tooltip?: string;
  size?: "sm" | "md";
  trend?: "up" | "down" | "flat";
  badge?: string;
}

const colorMap = {
  green:   "text-emerald-400",
  amber:   "text-amber-400",
  red:     "text-red-400",
  blue:    "text-indigo-400",
  default: "text-gray-100",
};

export function MetricCard({ label, value, subtitle, color = "default", tooltip, size = "md", badge }: MetricCardProps) {
  return (
    <div className="card-hover group relative">
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</span>
        {tooltip && (
          <div className="relative">
            <Info size={12} className="text-gray-600 cursor-help group-hover:text-gray-400 transition-colors" />
          </div>
        )}
      </div>
      <div className={clsx("font-bold mono leading-none", colorMap[color], size === "md" ? "text-2xl" : "text-xl")}>
        {value}
      </div>
      {subtitle && <div className="text-xs text-gray-500 mt-1.5">{subtitle}</div>}
      {badge && (
        <div className="absolute top-3 right-3">
          <span className="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded-md border border-gray-700">
            {badge}
          </span>
        </div>
      )}
    </div>
  );
}
