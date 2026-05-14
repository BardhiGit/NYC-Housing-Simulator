/**
 * Color-code financial metrics against NYC multifamily benchmarks.
 * Returns Tailwind color class: text-emerald-400 / text-amber-400 / text-red-400
 */

type Tier = "good" | "warn" | "bad" | "neutral";

function tier(t: Tier): string {
  switch (t) {
    case "good":    return "text-emerald-400";
    case "warn":    return "text-amber-400";
    case "bad":     return "text-red-400";
    case "neutral": return "text-gray-300";
  }
}

export function capRateColor(v: number): string {
  if (v >= 0.055) return tier("good");
  if (v >= 0.04)  return tier("warn");
  return tier("bad");
}

export function dscrColor(v: number): string {
  if (v >= 1.35) return tier("good");
  if (v >= 1.10) return tier("warn");
  return tier("bad");
}

export function cocColor(v: number): string {
  if (v >= 0.06) return tier("good");
  if (v >= 0.03) return tier("warn");
  return tier("bad");
}

export function breakEvenColor(v: number): string {
  if (v <= 0.80) return tier("good");
  if (v <= 0.90) return tier("warn");
  return tier("bad");
}

export function expenseRatioColor(v: number): string {
  if (v <= 0.50) return tier("good");
  if (v <= 0.65) return tier("warn");
  return tier("bad");
}

export function scoreColor(v: number): string {
  if (v >= 65) return tier("good");
  if (v >= 40) return tier("warn");
  return tier("bad");
}

export function cashFlowColor(v: number): string {
  if (v > 5_000)  return tier("good");
  if (v >= 0)     return tier("warn");
  return tier("bad");
}

export function irrColor(v: number): string {
  if (v >= 0.10) return tier("good");
  if (v >= 0.05) return tier("warn");
  return tier("bad");
}

/** Background color (fill) for score gauge zones */
export function scoreGaugeColor(v: number): string {
  if (v >= 65) return "#10b981";
  if (v >= 40) return "#f59e0b";
  return "#ef4444";
}

/** Letter grade color */
export function gradeColor(g: string): string {
  switch (g) {
    case "A": return "text-emerald-400";
    case "B": return "text-green-400";
    case "C": return "text-amber-400";
    case "D": return "text-orange-400";
    case "F": return "text-red-400";
    default:  return "text-gray-400";
  }
}
