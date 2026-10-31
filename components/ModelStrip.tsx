import type { Attempt, UsageRow } from "@/lib/types";
import { isNum, secs, usd } from "@/lib/format";

function chipText(u: UsageRow): string {
  const parts = [u.model];
  if (isNum(u.frames)) parts.push(`${u.frames} frames`);
  else if (isNum(u.tokens_out) && u.tokens_out > 0) parts.push(`${(u.tokens_in ?? 0) + u.tokens_out} tok`);
  if (isNum(u.latency_ms)) parts.push(secs(u.latency_ms));
  if (isNum(u.est_usd)) parts.push(usd(u.est_usd));
  return parts.join(" · ");
}

/** Every Meta call behind what is on screen, one chip per usage row. */
export function ModelStrip({
  rows,
  attempts,
  attemptModel,
  label = "Model calls",
}: {
  rows: UsageRow[];
  attempts?: Attempt[];
  attemptModel?: string;
  label?: string;
}) {
  const total =
    rows.reduce((s, r) => s + (isNum(r.est_usd) ? r.est_usd : 0), 0) +
    (attempts ?? []).reduce((s, a) => s + (isNum(a.est_usd) ? a.est_usd : 0), 0);
  const empty = rows.length === 0 && !(attempts && attempts.length);
  return (
    <div className="strip" aria-label={label}>
      <span className="strip__label">{label}</span>
      {empty ? <span className="muted">no model calls in this run</span> : null}
      <ul className="strip__chips">
        {rows.map((u, k) => (
          <li key={`${u.response_id ?? k}-${k}`} className="chip data" title={[u.feature, u.response_id].filter(Boolean).join(" · ")}>
            {chipText(u)}
          </li>
        ))}
        {(attempts ?? []).map((a) => (
          <li key={`att-${a.attempt}`} className="chip data" title={a.response_id ?? undefined}>
            {[attemptModel, `attempt ${a.attempt}`, isNum(a.minutes) ? `${(a.minutes * 60).toFixed(0)} s` : null, usd(a.est_usd)]
              .filter(Boolean)
              .join(" · ")}
          </li>
        ))}
      </ul>
      {!empty ? <span className="strip__total data">total {usd(total)}</span> : null}
    </div>
  );
}
