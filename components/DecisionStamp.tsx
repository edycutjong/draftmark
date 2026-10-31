import type { Decision, Warning } from "@/lib/types";

const TONE: Record<Decision, string> = {
  ISSUE: "issue",
  ISSUE_WITH_WARNING: "warn",
  REFUSE: "refuse",
  PROTEST: "refuse",
  NOT_SCORED: "muted",
};

/** The code-only decision: stamp + reason code + the API's hint text + every warning. */
export function DecisionStamp({
  decision,
  reason,
  hint,
  warnings,
  row,
  compact,
}: {
  decision: Decision;
  reason: string | null;
  hint: string | null;
  warnings?: Warning[];
  row?: number | null;
  compact?: boolean;
}) {
  return (
    <div className={`stamp stamp--${TONE[decision] ?? "muted"}${compact ? " stamp--compact" : ""}`}>
      <div className="stamp__head">
        <span className="stamp__word">{decision.replace(/_/g, " ")}</span>
        {reason ? <span className="stamp__reason data">{reason}</span> : null}
        {row != null ? <span className="stamp__row data">matrix row {row}</span> : null}
      </div>
      {hint ? <p className="stamp__hint">{hint}</p> : null}
      {warnings && warnings.length > 0 ? (
        <ul className="stamp__warnings">
          {warnings.map((w) => (
            <li key={w.code}>
              <span className="data">{w.code}</span> {w.hint}
              {w.detail ? <span className="muted"> ({w.detail})</span> : null}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
