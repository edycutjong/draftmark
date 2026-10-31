import { loadRun, runIndex } from "@/lib/runs";
import type { UsageRow } from "@/lib/types";
import { SiteHeader } from "@/components/SiteChrome";
import { HealthProbe } from "./HealthProbe";

export const dynamic = "force-static";
export const metadata = { title: "Evidence — DraftMark" };

/** /evidence — every Meta call behind the recorded runs (model, feature, latency, cost, response id) + a live health probe. */
export default function EvidencePage() {
  const rows: (UsageRow & { run: string })[] = [];
  for (const e of runIndex()) {
    const run = loadRun(e.run_id);
    for (const u of run?.usage ?? []) rows.push({ ...u, run: e.run_id });
  }
  const total = rows.reduce((s, r) => s + (r.est_usd ?? 0), 0);
  const byModel = new Map<string, { n: number; usd: number }>();
  for (const r of rows) {
    const m = byModel.get(r.model) ?? { n: 0, usd: 0 };
    byModel.set(r.model, { n: m.n + 1, usd: m.usd + (r.est_usd ?? 0) });
  }
  return (
    <>
      <SiteHeader />
      <main className="page">
        <h1 className="h1">Evidence</h1>
        <p className="lede">
          The Meta API calls behind the recorded runs on this site, as logged when they ran. Costs are price-list
          estimates, not an invoice. Longer write-ups live in the repository under <span className="data">evidence/</span>.
        </p>
        <h2 className="h2">Live deployment</h2>
        <HealthProbe />
        <h2 className="h2">Recorded Meta calls</h2>
        <p className="small muted swipe-hint">All rows are RECORDED calls from the runs on this site, not a live feed. Swipe the table sideways on a phone.</p>
        <div className="table-scroll table-scroll--fade" tabIndex={0} role="region" aria-label="Recorded Meta calls">
          <table className="table table--nowrap">
            <caption className="table__caption">
              {rows.length} calls · {[...byModel].map(([m, v]) => `${m} ×${v.n}`).join(" · ")} · est. ${total.toFixed(3)}
            </caption>
            <thead>
              <tr>
                <th scope="col">Run</th>
                <th scope="col">Model</th>
                <th scope="col">Latency</th>
                <th scope="col">Est. cost</th>
                <th scope="col">Feature</th>
                <th scope="col">Response id</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={`${r.run}-${i}`}>
                  <th scope="row" className="data">{r.run}</th>
                  <td className="data">{r.model}</td>
                  <td className="data">{r.latency_ms != null ? `${(r.latency_ms / 1000).toFixed(1)} s` : "—"}</td>
                  <td className="data">${(r.est_usd ?? 0).toFixed(4)}</td>
                  <td>{r.feature}</td>
                  <td className="data">{r.response_id || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </>
  );
}
