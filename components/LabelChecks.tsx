import type { Checks } from "@/lib/types";
import { fx } from "@/lib/format";

export const CHECK_KEYS = [
  ["monotone", "monotone"],
  ["pitch", "pitch"],
  ["residual", "residual"],
  ["cross_frame", "cross-frame"],
  ["anchor", "anchor"],
] as const;

export function CheckTicks({ checks }: { checks: Checks }) {
  return (
    <ul className="ticks" aria-label="Five code checks on the label reads">
      {CHECK_KEYS.map(([k, label]) => {
        const v = checks[k];
        return (
          <li key={k} className={v ? "tick tick--pass" : "tick tick--fail"}>
            <span aria-hidden="true">{v ? "✓" : "✗"}</span> {label}
            <span className="sr-only">{v ? " passed" : " failed"}</span>
          </li>
        );
      })}
    </ul>
  );
}

/** The label reads (per frame, by track) and the five code checks that gate them. */
export function LabelChecks({
  reads,
  checks,
  drafts,
  readBy,
  synthetic,
  typed,
}: {
  reads?: Record<string, Record<string, string>>;
  checks: Checks;
  drafts?: Record<string, number>;
  readBy?: string;
  synthetic?: boolean;
  typed?: boolean;
}) {
  const frames = Object.keys(reads ?? {});
  const tracks = Object.keys(drafts ?? checks.labels ?? {}).sort((a, b) => (drafts?.[a] ?? 0) - (drafts?.[b] ?? 0));
  const anchors = new Set(checks.anchor_tokens ?? []);
  return (
    <div className="labels">
      <p className="muted small">
        {synthetic
          ? "Synthetic labels: no model read these marks."
          : typed
            ? "Labels typed by hand (degraded run)."
            : `Read by ${readBy ?? "the label model"} on ${frames.length} frames; code checks decide.`}
      </p>
      <div className="table-scroll">
        <table className="table table--labels">
          <thead>
            <tr>
              <th scope="col">Token</th>
              {frames.map((f) => (
                <th scope="col" key={f}>
                  read · frame {f}
                </th>
              ))}
              <th scope="col">Confirmed</th>
              <th scope="col">Draft (m)</th>
            </tr>
          </thead>
          <tbody>
            {tracks.map((t) => (
              <tr key={t}>
                <th scope="row" className="data">
                  {t}
                  {anchors.has(t) ? <span className="anchor-tag">anchor</span> : null}
                </th>
                {frames.map((f) => (
                  <td key={f} className="data">
                    {reads?.[f]?.[t] ?? "—"}
                  </td>
                ))}
                <td className="mark-label">{checks.labels?.[t] ?? "—"}</td>
                <td className="data">{fx(drafts?.[t], Math.abs(drafts?.[t] ?? 2) < 1 ? 2 : 1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <CheckTicks checks={checks} />
      <p className="muted small data">
        pitch {fx(checks.pitch_px, 2)} px · fit residual {fx(checks.resid_rms_px, 2)} px · shared tokens {checks.shared ?? "—"}
        {checks.disagree && checks.disagree.length ? ` · disagree ${checks.disagree.join(", ")}` : ""}
      </p>
    </div>
  );
}
