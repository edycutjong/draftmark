"use client";
import { useEffect, useState } from "react";

type Health = { ok: boolean; version: string; models: string[]; live_mode: string; budget: string | null };

/** Calls the deployed /api/py/health so the page proves the Python functions are up right now. */
export function HealthProbe() {
  const [h, setH] = useState<Health | "error" | null>(null);
  useEffect(() => {
    fetch("/api/py/health")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setH)
      .catch(() => setH("error"));
  }, []);
  if (h === null) return <p className="muted" role="status">Checking the API…</p>;
  if (h === "error") return <p role="alert">The API did not answer. The recorded runs still render.</p>;
  return (
    <dl className="kv" aria-live="polite">
      <div><dt>API</dt><dd className="data">{h.ok ? "up" : "down"} · {h.version}</dd></div>
      <div><dt>Models wired</dt><dd className="data">{h.models.join(", ")}</dd></div>
      <div><dt>Live mode</dt><dd className="data">{h.live_mode}{h.budget ? ` · budget flag: ${h.budget}` : ""}</dd></div>
    </dl>
  );
}
