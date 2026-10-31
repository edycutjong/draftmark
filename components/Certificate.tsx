import type { ReactNode } from "react";
import type { Run } from "@/lib/types";
import { DASH, fx, grouped, isNum, shortSha, tiny } from "@/lib/format";
import { DecisionStamp } from "./DecisionStamp";
import { CheckTicks } from "./LabelChecks";
import { SurveyResult } from "./SurveyResult";
import { ModelStrip } from "./ModelStrip";
import { Badge, Badges } from "./Badge";
import { WaveChart } from "./WaveChart";

function Line({ n, title, children }: { n: string; title: string; children: ReactNode }) {
  return (
    <section className="cert__section" aria-labelledby={`cert-${n}`}>
      <h2 id={`cert-${n}`} className="cert__h">
        <span className="cert__n data">{n}</span> {title}
      </h2>
      <div className="cert__body">{children}</div>
    </section>
  );
}

const PROOF_TEXT: Record<string, string> = {
  booklet: "booklet — the survey program reproduced the stability booklet's printed conditions (no scale truth)",
  scale: "scale — measurement proof against a weighed load",
};

/** Printable certificate. Every value comes from the run JSON; nothing here computes a figure. */
export function Certificate({ run }: { run: Run }) {
  const c = run.certificate;
  const r = run.draft?.result;
  const d = c.draft;
  const refused = c.decision === "REFUSE";
  const st = c.selftest;
  return (
    <article className="cert">
      <header className="cert__top">
        <div>
          <p className="eyebrow">Draft survey certificate</p>
          <h1 className="cert__title">{run.title}</h1>
        </div>
        <Badges>
          <Badge tone={c.mode === "LIVE" ? "live" : "recorded"}>{c.mode}</Badge>
          {run.kind === "synthetic" ? <Badge tone="synthetic">SYNTHETIC geometry — not SAM, not the kitchen scale</Badge> : null}
          {run.kind === "public-clip" ? <Badge tone="caveat">third-party test clip · no ground truth · frames not re-hosted</Badge> : null}
          {c.proof === "booklet" ? <Badge tone="proof">no scale truth</Badge> : null}
        </Badges>
      </header>

      <Line n="001" title="Identification">
        <dl className="kv">
          <div>
            <dt>Run id</dt>
            <dd className="data">{c.run_id}</dd>
          </div>
          <div>
            <dt>Run mode</dt>
            <dd className="data">{c.mode}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd className="data">{c.created_at}</dd>
          </div>
          <div>
            <dt>Vessel mode</dt>
            <dd className="data">{c.vessel_mode}</dd>
          </div>
          <div>
            <dt>Proof kind</dt>
            <dd>
              <span className="data">{c.proof}</span> · {PROOF_TEXT[c.proof] ?? DASH}
            </dd>
          </div>
          {c.clip ? (
            <div>
              <dt>Measured on</dt>
              <dd>
                <span className="data">{c.clip.id}</span>
                {c.clip.source?.startsWith("http") ? (
                  <>
                    {" "}
                    · <a href={c.clip.source}>source</a>
                  </>
                ) : c.clip.source ? (
                  <span className="muted"> · {c.clip.source}</span>
                ) : null}
                {c.clip.note ? <span className="muted"> · {c.clip.note}</span> : null}
              </dd>
            </div>
          ) : null}
          {c.booklet ? (
            <div>
              <dt>Booklet</dt>
              <dd className="data">
                {c.booklet.id} · condition {c.booklet.condition} · p. {c.booklet.page}
              </dd>
            </div>
          ) : null}
        </dl>
      </Line>

      <Line n="010" title="Decision">
        <DecisionStamp decision={c.decision} reason={c.reason} hint={c.hint} warnings={c.warnings} row={c.decision_row} />
      </Line>

      <Line n="020" title="Draft measurement">
        {d && isNum(d.d_m) ? (
          <>
            <dl className="kv">
              <div>
                <dt>Draft d</dt>
                <dd className="data">{fx(d.d_m)} m</dd>
              </div>
              <div>
                <dt>Repeatability u (k=1)</dt>
                <dd className="data">± {fx(d.u_rep_m)} m</dd>
              </div>
              <div>
                <dt>Absolute u (k=1)</dt>
                <dd className="data">{isNum(d.u_abs_m) ? `± ${fx(d.u_abs_m)} m` : "not stated — no ground truth"}</dd>
              </div>
              {r?.u_parts ? (
                <div>
                  <dt>u parts</dt>
                  <dd className="data">
                    swell {fx(r.u_parts.swell)} · random {fx(r.u_parts.rand)}
                    {r.u_parts.sys
                      ? Object.entries(r.u_parts.sys)
                          .map(([k, v]) => ` · ${k} ${fx(v)}`)
                          .join("")
                      : ""}
                  </dd>
                </div>
              ) : null}
              <div>
                <dt>Frames used</dt>
                <dd className="data">
                  {d.n_kept} / {d.n_frames}
                  {d.drops && Object.keys(d.drops).length
                    ? ` · dropped ${Object.entries(d.drops)
                        .map(([k, v]) => `${k} × ${v}`)
                        .join(", ")}`
                    : ""}
                </dd>
              </div>
              <div>
                <dt>
                  N<sub>eff</sub> · lag-1 ρ
                </dt>
                <dd className="data">
                  {fx(d.n_eff, 2)} · {fx(d.rho1, 3)}
                </dd>
              </div>
              <div>
                <dt>Swell p5–p95</dt>
                <dd className="data">{d.swell_p5_p95 ? `${fx(d.swell_p5_p95[0])} – ${fx(d.swell_p5_p95[1])} m` : DASH}</dd>
              </div>
              <div>
                <dt>One-pitch label shift</dt>
                <dd className="data">moves d by {fx(d.label_shift_sensitivity_m, 2)} m</dd>
              </div>
            </dl>
            {r && run.draft?.frames?.length ? (
              <div className="cert__wave">
                <WaveChart
                  id={`cert-${c.run_id}`}
                  frames={run.draft.frames}
                  result={r}
                  markScale={run.geometry?.mark_system.scale ?? (c.vessel_mode === "barge" ? 0.1 : 1)}
                  animate={false}
                  small
                />
              </div>
            ) : null}
          </>
        ) : (
          <p>No clip measurement in this run: every draft position was entered.</p>
        )}
      </Line>

      {c.labels ? (
        <Line n="030" title="Mark labels">
          <p className="small">
            Read by <span className="data">{c.labels.read_by}</span>
            {c.labels.degraded ? " · degraded: labels by hand" : ""}
          </p>
          {c.labels.checks ? <CheckTicks checks={c.labels.checks} /> : null}
        </Line>
      ) : null}

      <Line n="040" title="Survey">
        {c.survey ? (
          <>
            <SurveyResult survey={c.survey} booklet={c.booklet} />
            {refused ? (
              <p className="refused-note">
                Displacement, deductions, net and cargo are not printed: the decision is REFUSE (
                <span className="data">{c.reason}</span>).
              </p>
            ) : null}
          </>
        ) : (
          <p>{DASH}</p>
        )}
      </Line>

      <Line n="050" title="Survey program">
        <dl className="kv">
          <div>
            <dt>Program author</dt>
            <dd className="data">{c.program_author ?? DASH}</dd>
          </div>
          <div>
            <dt>Regenerations</dt>
            <dd className="data">{c.regen_count ?? DASH}</dd>
          </div>
          <div>
            <dt>Response id</dt>
            <dd className="data">{c.response_id ?? DASH}</dd>
          </div>
          {c.survey?.program_sha ? (
            <div>
              <dt>Program sha256</dt>
              <dd className="data">{shortSha(c.survey.program_sha, 24)}</dd>
            </div>
          ) : null}
          {st ? (
            <div>
              <dt>Self-test verdict</dt>
              <dd className="data">
                {st.verdict} · {st.pass_count}/{st.n} printed conditions · probes{" "}
                {(st.probes_raised ?? []).filter(Boolean).length}/{(st.probes_raised ?? []).length} · differential{" "}
                {st.differential_n} cases, max {tiny(st.differential_max_err_pct)} %
                {st.fallback ? ` · fallback ${st.fallback}` : ""}
              </dd>
            </div>
          ) : (
            <div>
              <dt>Self-test</dt>
              <dd>not applicable: {c.survey?.program_author ?? "analytic"} geometry, no model-written program</dd>
            </div>
          )}
          {c.survey?.barge ? (
            <div>
              <dt>Barge geometry</dt>
              <dd className="data">
                L {fx(c.survey.barge.L_m, 3)} m · B {fx(c.survey.barge.B_m, 3)} m · light {grouped(c.survey.barge.light_kg, 3)} kg ·
                ρ {fx(c.survey.barge.rho_kg_m3, 1)} kg/m³{c.survey.booklet_id ? ` · ${c.survey.booklet_id}` : ""}
              </dd>
            </div>
          ) : null}
        </dl>
      </Line>

      <Line n="060" title="Models">
        <p className="data">{c.models.join(" · ")}</p>
        {run.usage && run.usage.length ? <ModelStrip rows={run.usage} label="Calls in this run" /> : null}
      </Line>

      <footer className="cert__footer">
        <p className="data small">
          {c.run_id} · {c.mode} · proof: {c.proof}
        </p>
        <p className="cert__disclaimer">{c.footer}</p>
      </footer>
    </article>
  );
}
