/** Format a number as USD currency. */
export function formatCurrency(v: number | null | undefined, decimals = 0): string {
  if (v == null || isNaN(v)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(v);
}

/** Format as percentage (0.0675 → "6.75%"). */
export function formatPct(v: number | null | undefined, decimals = 2): string {
  if (v == null || isNaN(v)) return "—";
  return `${(v * 100).toFixed(decimals)}%`;
}

/** Format as a multiplier (1.82 → "1.82×"). */
export function formatMultiple(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return "—";
  return `${v.toFixed(2)}×`;
}

/** Format DSCR with two decimals (1.35 → "1.35×"). */
export function formatDSCR(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return "—";
  if (!isFinite(v)) return "∞";
  return `${v.toFixed(2)}×`;
}

/** Compact number (1,250,000 → "$1.25M"). */
export function formatCompact(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return "—";
  const abs = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(0)}K`;
  return formatCurrency(v);
}

/** Number with commas (1250000 → "1,250,000"). */
export function formatNumber(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return "—";
  return new Intl.NumberFormat("en-US").format(Math.round(v));
}
