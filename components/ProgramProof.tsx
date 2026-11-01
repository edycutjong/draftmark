"use client";

import { useState } from "react";
import type { Attempt, Program, Selftest } from "@/lib/types";
import { api, REASON_NEXT, type Reason } from "@/lib/api";
import { DASH, fx, shortSha, tiny, usd } from "@/lib/format";
import { Badge } from "./Badge";
import { SelfTestTable, SelfTestVerdict } from "./SelfTestTable";

function AttemptPanel({ a }: { a: Attempt }) {
  return (
    <div className="attempt">
      <p className={`verdict ${a.verdict === "PASS" ? "verdict--pass" : "verdict--fail"}`}>
        <span className="verdict__word">{a.verdict}</span>
        <span className="data">
          {a.pass_count}/{a.n} printed conditions
        </span>
        {a.diff_max != null ? <span className="data">differential max error {tiny(a.diff_max)} %</span> : null}
      </p>
      {a.error ? <p className="attempt__error data">{a.error}</p> : null}
      {a.failing && a.failing.length ? (
        <p className="small">
          Failing conditions and their first diverging intermediate:{" "}
          <span className="data">{a.failing.map(([c, k]) => `${c} → ${k}`).join(" · ")}</span>
        </p>
      ) : null}
      <p className="muted small data">
        {a.minutes != null ? `${fx(a.minutes, 2)} min` : DASH} · {usd(a.est_usd)} · {a.usage?.total_tokens ?? DASH} tokens ·{" "}
        {a.response_id ?? DASH} · sha {shortSha(a.sha)}
      </p>
    </div>
  );
}

/** Program proof: the model-written survey program must reproduce the booklet's printed conditions in the
 *  sandbox before it may compute anything. Shown identically on the recorded page and in the live flow. */
export function ProgramProof({ program, selftest, live }: { program: Program; selftest: Selftest; live?: boolean }) {
  const attempts = program.attempts?.attempts ?? [];
  const [tab, setTab] = useState(attempts.length ? attempts.length - 1 : 0);
  const [st, setSt] = useState<Selftest>(selftest);
  const [rerun, setRerun] = useState<{ state: "idle" | "busy" | "done" | "error"; ms?: number; reason?: Reason; detail?: string }>({
    state: "idle",
  });

  async function onRerun() {
    setRerun({ state: "busy" });
    const r = await api<{ ok: true; selftest: Selftest }>("selftest/rerun", {});
    if (r.ok) {
      setSt(r.data.selftest);
      setRerun({ state: "done", ms: r.ms });
    } else setRerun({ state: "error", reason: r.reason, detail: r.detail });
  }

  return (
    <div className="proof">
      <div className="proof__meta">
        <dl className="kv kv--inline">
          <div>
            <dt>Program author</dt>
            <dd className="data">{program.meta.program_author}</dd>
          </div>
          <div>
            <dt>Response id</dt>
            <dd className="data">{program.meta.response_id ?? DASH}</dd>
          </div>
          <div>
            <dt>sha256</dt>
            <dd className="data" title={program.meta.sha256}>
              {shortSha(program.meta.sha256, 16)}
            </dd>
          </div>
          <div>
            <dt>Regenerations</dt>
            <dd className="data">{program.meta.regen_count ?? DASH}</dd>
          </div>
        </dl>
      </div>

      <h3 className="h4">Self-test on the printed conditions</h3>
      <SelfTestVerdict st={st} />
      <div className="proof__actions">
        <button type="button" className="btn" onClick={onRerun} disabled={rerun.state === "busy"}>
          {rerun.state === "busy" ? "Re-running in the sandbox…" : "Re-run self-test live (sandbox, no API cost)"}
        </button>
        {rerun.state === "done" ? (
          <span className="small">
            <Badge tone="live">LIVE</Badge> re-run just now · sandbox {st.wall_ms ?? DASH} ms · round trip {rerun.ms} ms
          </span>
        ) : null}
        {rerun.state === "error" && rerun.reason ? (
          <span className="error-inline small" role="alert">
            <span className="data">{rerun.reason}</span> {rerun.detail} — {REASON_NEXT[rerun.reason]}
          </span>
        ) : null}
        {live && rerun.state === "idle" ? <span className="muted small">recorded self-test of the cached program</span> : null}
      </div>
      <SelfTestTable rows={st.rows ?? []} />

      {attempts.length ? (
        <>
          <h3 id="attempts-h" className="h4">How the program was earned</h3>
          <div className="tabs" role="tablist" aria-label="Generation attempts">
            {attempts.map((a, k) => (
              <button
                key={a.attempt}
                type="button"
                role="tab"
                id={`att-tab-${a.attempt}`}
                aria-selected={tab === k}
                aria-controls={`att-panel-${a.attempt}`}
                className={`tab ${a.verdict === "PASS" ? "tab--pass" : "tab--fail"}`}
                onClick={() => setTab(k)}
              >
                Attempt {a.attempt} · {a.verdict === "PASS" ? `${a.pass_count}/${a.n}` : a.pass_count === 0 && a.error ? "gate reject" : `${a.pass_count}/${a.n}`}
              </button>
            ))}
          </div>
          {attempts[tab] ? (
            <div role="tabpanel" id={`att-panel-${attempts[tab].attempt}`} aria-labelledby={`att-tab-${attempts[tab].attempt}`}>
              <AttemptPanel a={attempts[tab]} />
            </div>
          ) : null}
          {program.meta.note ? <p className="muted small">{program.meta.note}</p> : null}
        </>
      ) : null}

      <details className="code">
        <summary>
          Proven program source <span className="data muted">({program.code.trimEnd().split("\n").length} lines)</span>
        </summary>
        <pre>
          <code>{program.code}</code>
        </pre>
      </details>
    </div>
  );
}
