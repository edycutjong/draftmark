/** Display formatting only: every value passed in comes from JSON or an API response. */

export const DASH = "—";

export function isNum(x: unknown): x is number {
  return typeof x === "number" && Number.isFinite(x);
}

/** Fixed decimals; drafts below 1 m (the 1:10 barge strip) get one more decimal by default. */
export function fx(x: unknown, digits?: number): string {
  if (!isNum(x)) return DASH;
  const d = digits ?? (Math.abs(x) < 1 ? 4 : 3);
  return x.toFixed(d);
}

/** Thousands-separated with fixed decimals (tonnes, kilograms). */
export function grouped(x: unknown, digits = 1): string {
  if (!isNum(x)) return DASH;
  return x.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function pct(x: unknown, digits = 3): string {
  if (!isNum(x)) return DASH;
  return `${x.toFixed(digits)} %`;
}

export function usd(x: unknown): string {
  if (!isNum(x)) return DASH;
  if (x === 0) return "$0";
  return x < 0.01 ? `$${x.toFixed(4)}` : `$${x.toFixed(3)}`;
}

export function secs(ms: unknown): string {
  if (!isNum(ms)) return DASH;
  return `${(ms / 1000).toFixed(1)} s`;
}

/** Signed value with explicit + for corrections. */
export function signed(x: unknown, digits = 3): string {
  if (!isNum(x)) return DASH;
  return `${x >= 0 ? "+" : "−"}${Math.abs(x).toFixed(digits)}`;
}

export function shortSha(s: unknown, n = 12): string {
  return typeof s === "string" && s.length > n ? `${s.slice(0, n)}…` : typeof s === "string" ? s : DASH;
}

/** Engineering exponent for tiny percentages (differential max error). */
export function tiny(x: unknown): string {
  if (!isNum(x)) return DASH;
  return Math.abs(x) < 0.001 && x !== 0 ? x.toExponential(1) : x.toFixed(4);
}

export const POSITIONS = ["fore_p", "fore_s", "mid_p", "mid_s", "aft_p", "aft_s"] as const;
export type Position = (typeof POSITIONS)[number];
export const POSITION_LABEL: Record<Position, string> = {
  fore_p: "Fore P",
  fore_s: "Fore S",
  mid_p: "Mid P",
  mid_s: "Mid S",
  aft_p: "Aft P",
  aft_s: "Aft S",
};
