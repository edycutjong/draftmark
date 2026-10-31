import type { DraftResult } from "@/lib/types";
import { DASH, fx, isNum } from "@/lib/format";

/** Clip result: d ± u with repeatability and absolute uncertainty shown apart, frame accounting, swell. */
export function ResultCard({ result, noTruth }: { result: DraftResult; noTruth?: boolean }) {
  const drops = Object.entries(result.drops ?? {});
  const sys = result.u_parts?.sys;
  return (
    <div className="result">
      <div className="result__head">
        <span className="result__label">Draft d</span>
        <span className="result__value">
          {fx(result.d_m)}
          <span className="result__unit"> m</span>
        </span>
      </div>
      <dl className="kv">
        <div>
          <dt>Repeatability u (k=1)</dt>
          <dd className="data">± {fx(result.u_rep_m)} m</dd>
        </div>
        <div>
          <dt>Absolute u (k=1)</dt>
          <dd className="data">
            {isNum(result.u_abs_m) ? `± ${fx(result.u_abs_m)} m` : noTruth ? "not stated — no ground truth" : DASH}
          </dd>
        </div>
        {result.u_parts ? (
          <div>
            <dt>u parts</dt>
            <dd className="data">
              swell {fx(result.u_parts.swell)} · random {fx(result.u_parts.rand)}
              {sys
                ? Object.entries(sys)
                    .map(([k, v]) => ` · ${k} ${fx(v)}`)
                    .join("")
                : ""}
            </dd>
          </div>
        ) : null}
        <div>
          <dt>Frames kept</dt>
          <dd className="data">
            {result.n_kept ?? DASH} / {result.n_frames ?? DASH}
          </dd>
        </div>
        <div>
          <dt>Dropped (reason)</dt>
          <dd className="data">
            {drops.length ? drops.map(([k, v]) => `${k} × ${v}`).join(" · ") : "none"}
          </dd>
        </div>
        <div>
          <dt>
            N<sub>eff</sub> · lag-1 ρ
          </dt>
          <dd className="data">
            {fx(result.n_eff, 2)} · {fx(result.rho1, 3)}
          </dd>
        </div>
        <div>
          <dt>Swell p5–p95</dt>
          <dd className="data">
            {result.swell_p5_p95 ? `${fx(result.swell_p5_p95[0])} – ${fx(result.swell_p5_p95[1])} m` : DASH}
          </dd>
        </div>
        <div>
          <dt>One-pitch label shift</dt>
          <dd className="data">moves d by {fx(result.label_shift_sensitivity_m, 2)} m</dd>
        </div>
      </dl>
    </div>
  );
}
