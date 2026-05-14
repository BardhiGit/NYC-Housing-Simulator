"use client";

import { AlertTriangle, AlertCircle, Info, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { SeverityBadge } from "@/components/ui/badge";
import type { RedFlag } from "@/lib/types/financial";

const icons = {
  CRITICAL: AlertCircle,
  HIGH:     AlertTriangle,
  MEDIUM:   AlertTriangle,
  LOW:      Info,
};

export function RedFlagList({ flags }: { flags: RedFlag[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (!flags.length) {
    return (
      <div className="card flex items-center gap-3 text-sm text-emerald-400">
        <div className="w-2 h-2 rounded-full bg-emerald-400" />
        No red flags detected — this property passes all threshold checks.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {flags.map((flag) => {
        const Icon = icons[flag.severity];
        const isOpen = expanded === flag.code;
        return (
          <div
            key={flag.code}
            className="card border-l-2"
            style={{
              borderLeftColor:
                flag.severity === "CRITICAL" ? "#ef4444" :
                flag.severity === "HIGH"     ? "#f97316" :
                flag.severity === "MEDIUM"   ? "#f59e0b" : "#3b82f6",
            }}
          >
            <button
              className="w-full flex items-start gap-3 text-left"
              onClick={() => setExpanded(isOpen ? null : flag.code)}
            >
              <Icon
                size={15}
                className="mt-0.5 flex-none"
                style={{
                  color: flag.severity === "CRITICAL" ? "#f87171" :
                         flag.severity === "HIGH"     ? "#fb923c" :
                         flag.severity === "MEDIUM"   ? "#fbbf24" : "#60a5fa",
                }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-gray-100">{flag.title}</span>
                  <SeverityBadge severity={flag.severity} />
                  <span className="text-xs text-gray-500 ml-auto">{flag.current_value}</span>
                </div>
                <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{flag.description}</p>
              </div>
              {isOpen ? <ChevronUp size={14} className="text-gray-600 mt-0.5" /> : <ChevronDown size={14} className="text-gray-600 mt-0.5" />}
            </button>
            {isOpen && (
              <div className="mt-3 pt-3 border-t border-gray-800 grid grid-cols-2 gap-3 text-xs">
                <div>
                  <div className="text-gray-500 mb-0.5">Threshold</div>
                  <div className="text-gray-300">{flag.threshold}</div>
                </div>
                <div>
                  <div className="text-gray-500 mb-0.5">Recommendation</div>
                  <div className="text-gray-300">{flag.recommendation}</div>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
