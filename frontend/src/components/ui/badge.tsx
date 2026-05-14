import { clsx } from "clsx";
import type { RentType } from "@/lib/types/property";

interface BadgeProps { children: React.ReactNode; variant?: "default" | "success" | "warn" | "danger" | "info"; className?: string; }

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span className={clsx(
      "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
      variant === "default" && "bg-gray-700/60 text-gray-300 border-gray-600",
      variant === "success" && "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
      variant === "warn"    && "bg-amber-500/15 text-amber-400 border-amber-500/30",
      variant === "danger"  && "bg-red-500/15 text-red-400 border-red-500/30",
      variant === "info"    && "bg-indigo-500/15 text-indigo-400 border-indigo-500/30",
      className,
    )}>
      {children}
    </span>
  );
}

export function RentTypeBadge({ type }: { type: RentType }) {
  const map: Record<RentType, { cls: string; label: string }> = {
    stabilized:     { cls: "badge-rs",     label: "RS" },
    free_market:    { cls: "badge-fm",     label: "FM" },
    vacant:         { cls: "badge-vacant", label: "Vacant" },
    owner_occupied: { cls: "badge-owner",  label: "Owner" },
  };
  const { cls, label } = map[type] ?? { cls: "badge-owner", label: type };
  return <span className={cls}>{label}</span>;
}

export function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, { cls: string }> = {
    CRITICAL: { cls: "bg-red-500/20 text-red-300 border-red-500/30" },
    HIGH:     { cls: "bg-orange-500/20 text-orange-300 border-orange-500/30" },
    MEDIUM:   { cls: "bg-amber-500/20 text-amber-300 border-amber-500/30" },
    LOW:      { cls: "bg-blue-500/20 text-blue-300 border-blue-500/30" },
  };
  const { cls } = map[severity] ?? { cls: "bg-gray-700 text-gray-300 border-gray-600" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {severity}
    </span>
  );
}
