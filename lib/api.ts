/** Fetch wrapper for /api/py/*: every failure comes back as a reason code the UI can render. */

export type Reason =
  | "PAYLOAD"
  | "JUDGE_CODE"
  | "BUDGET"
  | "RATE"
  | "UPSTREAM"
  | "NO_FIXTURE"
  | "TIMEOUT"
  | "NO_EVIDENCE"
  | "LABEL_FRAMES"
  | "UNSIGNED"
  | "NO_BOOKLET";

export type ApiResult<T> = { ok: true; data: T; ms: number } | { ok: false; reason: Reason; detail: string; ms: number };

export const TIMEOUT_MS = 280_000;

const KNOWN: Reason[] = ["PAYLOAD", "JUDGE_CODE", "BUDGET", "RATE", "UPSTREAM", "NO_FIXTURE", "TIMEOUT", "NO_EVIDENCE",
  "LABEL_FRAMES", "UNSIGNED", "NO_BOOKLET"];

export async function api<T>(path: string, body?: unknown, timeoutMs = TIMEOUT_MS): Promise<ApiResult<T>> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  const t0 = performance.now();
  const ms = () => Math.round(performance.now() - t0);
  try {
    const res = await fetch(`/api/py/${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? undefined : { "content-type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: ctrl.signal,
    });
    let json: Record<string, unknown> | null = null;
    try {
      json = (await res.json()) as Record<string, unknown>;
    } catch {
      json = null;
    }
    if (json && json.ok === false) {
      const r = String(json.reason ?? "UPSTREAM") as Reason;
      return { ok: false, reason: KNOWN.includes(r) ? r : "UPSTREAM", detail: String(json.detail ?? ""), ms: ms() };
    }
    if (!res.ok || !json) {
      const reason: Reason = res.status === 413 || res.status === 415 ? "PAYLOAD" : res.status === 429 ? "RATE" : "UPSTREAM";
      return { ok: false, reason, detail: `HTTP ${res.status}`, ms: ms() };
    }
    return { ok: true, data: json as T, ms: ms() };
  } catch (e) {
    if ((e as Error).name === "AbortError") {
      return { ok: false, reason: "TIMEOUT", detail: `no response after ${Math.round(timeoutMs / 1000)} s`, ms: ms() };
    }
    return { ok: false, reason: "UPSTREAM", detail: (e as Error).message || "network error", ms: ms() };
  } finally {
    clearTimeout(timer);
  }
}

/** What the user can do next, per reason (layout guidance; decision hints come from the API). */
export const REASON_NEXT: Record<Reason, string> = {
  PAYLOAD: "The request was rejected before any model call: check the clip (MP4, size, length) or frame size.",
  NO_EVIDENCE: "A certificate needs a measured clip (or a ship survey on a named booklet).",
  LABEL_FRAMES: "Send exactly the two label frames chosen by the measure step.",
  JUDGE_CODE: "Uploads need the judge code from the submission notes.",
  BUDGET: "Live runs are off on this deployment right now. Open the recorded run instead.",
  RATE: "Too many live runs from this address. Wait a minute, or open the recorded run.",
  UPSTREAM: "The Meta API call failed. Try again, or open the recorded run.",
  NO_FIXTURE: "That fixture clip is not on this deployment.",
  TIMEOUT: "The call ran past the function limit. Open the recorded run, or try a shorter clip.",
  UNSIGNED: "This measurement was not produced by this server's stations (or was edited): measure the clip again.",
  NO_BOOKLET: "That vessel booklet is not on this deployment.",
};

export const LOCAL_RUN_KEY = "draftmark:run:local";
