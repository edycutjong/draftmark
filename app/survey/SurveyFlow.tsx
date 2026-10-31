"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api, LOCAL_RUN_KEY, REASON_NEXT, type Reason } from "@/lib/api";
import { BARGE_WHAT_IF_SG, MARK_SYSTEMS, MAX_BYTES, MAX_FPS, MAX_FRAMES, MAX_SECONDS, SHIP_SG, type MarkSystemId } from "@/lib/limits";
import { DASH, POSITIONS, POSITION_LABEL, fx, isNum, type Position } from "@/lib/format";
import type { Certificate, ClipInfo, DraftFrame, DraftResult, Geometry, Labels, Program, Run, Selftest, UsageRow } from "@/lib/types";
import { Badge } from "@/components/Badge";
import { Overlay } from "@/components/Overlay";
import { WaveChart } from "@/components/WaveChart";
import { ResultCard } from "@/components/ResultCard";
import { LabelChecks } from "@/components/LabelChecks";
import { ProgramProof } from "@/components/ProgramProof";
import { DecisionStamp } from "@/components/DecisionStamp";
import { SurveyResult } from "@/components/SurveyResult";
import { ModelStrip } from "@/components/ModelStrip";

type Err = { reason: Reason; detail: string };
type Async<T> = { state: "idle" } | { state: "busy"; t0: number } | { state: "done"; data: T; ms: number } | { state: "error"; err: Err };

interface Health {
  ok: boolean;
  fixtures: string[];
  key_present?: boolean;
  live_mode?: string;
  budget?: string | null;
  models?: string[];
}
interface MeasureResp {
  run_id: string;
  clip: ClipInfo;
  geometry: Geometry;
  row1_hint?: string | null;
  usage: UsageRow[];
  timing_ms?: Record<string, number>;
}
interface DraftResp {
  result: DraftResult;
  frames: DraftFrame[];
  row1: string | null;
}
type ProgramResp = Program & { selftest: Selftest; run?: string };

/* ---------- small pieces ---------- */

function Station({
  n,
  title,
  open,
  done,
  live,
  children,
  note,
}: {
  n: number;
  title: string;
  open: boolean;
  done?: boolean;
  live?: boolean;
  children?: ReactNode;
  note?: string;
}) {
  return (
    <section className={`station${open ? " station--open" : ""}${done ? " station--done" : ""}`} aria-labelledby={`st-${n}`}>
      <header className="station__head">
        <span className="station__n" aria-hidden="true">
          {n}
        </span>
        <h2 id={`st-${n}`} className="station__title">
          <span className="sr-only">Step {n}: </span>
          {title}
        </h2>
        {live && open ? <Badge tone="live">LIVE</Badge> : null}
        {done ? <span className="station__done">done</span> : null}
      </header>
      {open ? <div className="station__body">{children}</div> : <p className="station__locked muted small">{note ?? `Opens after step ${n - 1}.`}</p>}
    </section>
  );
}

function ErrorBox({ err }: { err: Err }) {
  const detail = err.detail.length > 160 ? `${err.detail.slice(0, 157)}…` : err.detail;
  return (
    <div className="error-box" role="alert">
      <p>
        <span className="data error-box__code">{err.reason}</span> {detail}
      </p>
      <p className="small">
        {REASON_NEXT[err.reason]} <Link href="/">Open the recorded runs →</Link>
      </p>
    </div>
  );
}

function Elapsed({ t0 }: { t0: number }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(id);
  }, []);
  return <span className="data">{((now - t0) / 1000).toFixed(1)} s</span>;
}

function seek(v: HTMLVideoElement, t: number): Promise<void> {
  return new Promise((resolve) => {
    if (Math.abs(v.currentTime - t) < 1e-3 && v.readyState >= 2) return resolve();
    const done = () => {
      v.removeEventListener("seeked", done);
      resolve();
    };
    v.addEventListener("seeked", done);
    v.currentTime = t;
  });
}

function readDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result));
    r.onerror = () => reject(r.error);
    r.readAsDataURL(file);
  });
}

const num = (s: string): number | undefined => (s.trim() === "" || !Number.isFinite(Number(s)) ? undefined : Number(s));

/* ---------- the flow ---------- */

export function SurveyFlow() {
  const [health, setHealth] = useState<Async<Health>>({ state: "idle" });
  const [usage, setUsage] = useState<UsageRow[]>([]);
  const runId = useRef(`live-${Date.now().toString(36)}`);

  // station 1: clip
  const [file, setFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [meta, setMeta] = useState<{ w: number; h: number; dur: number } | null>(null);
  const [fps, setFps] = useState("6");
  const [system, setSystem] = useState<MarkSystemId>("ship");
  const [judgeCode, setJudgeCode] = useState("");
  const [fixture, setFixture] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // stations 2-6
  const [measure, setMeasure] = useState<Async<MeasureResp>>({ state: "idle" });
  const [frameIdx, setFrameIdx] = useState(0);
  const [labels, setLabels] = useState<Async<Labels>>({ state: "idle" });
  const [frameShots, setFrameShots] = useState<Record<number, string>>({});
  const [anchor, setAnchor] = useState<"pending" | "confirmed" | "rejected">("pending");
  const [typed, setTyped] = useState<Record<string, string>>({});
  const [typedRes, setTypedRes] = useState<Async<Labels>>({ state: "idle" });
  const [finalLabels, setFinalLabels] = useState<Labels | null>(null);
  const [draft, setDraft] = useState<Async<DraftResp>>({ state: "idle" });
  const [program, setProgram] = useState<Async<ProgramResp>>({ state: "idle" });

  useEffect(() => {
    setHealth({ state: "busy", t0: Date.now() });
    api<Health>("health", undefined, 20_000).then((r) =>
      setHealth(r.ok ? { state: "done", data: r.data, ms: r.ms } : { state: "error", err: { reason: r.reason, detail: r.detail } }),
    );
  }, []);

  useEffect(() => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    setVideoUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const fpsNum = num(fps);
  const nFrames = meta && fpsNum ? Math.round(meta.dur * fpsNum) : 0;
  const clipProblems = useMemo(() => {
    const p: string[] = [];
    if (!file) return p;
    if (file.type !== "video/mp4") p.push(`MP4 only (this file is ${file.type || "an unknown type"}).`);
    if (file.size > MAX_BYTES) p.push(`${(file.size / 1048576).toFixed(2)} MB is over the ${MAX_BYTES / 1048576} MB limit.`);
    if (meta && meta.dur > MAX_SECONDS + 0.05) p.push(`${meta.dur.toFixed(2)} s is longer than ${MAX_SECONDS} s.`);
    if (!fpsNum || fpsNum <= 0 || fpsNum > MAX_FPS) p.push(`Frame rate must be between 1 and ${MAX_FPS} fps.`);
    if (nFrames > MAX_FRAMES) p.push(`${nFrames} frames is more than ${MAX_FRAMES}.`);
    if (!judgeCode.trim()) p.push("Enter the judge code.");
    return p;
  }, [file, meta, fpsNum, nFrames, judgeCode]);

  const pushUsage = useCallback((rows?: UsageRow[]) => {
    if (rows && rows.length) setUsage((u) => [...u, ...rows]);
  }, []);

  function resetAfterClip() {
    setMeasure({ state: "idle" });
    setLabels({ state: "idle" });
    setFrameShots({});
    setAnchor("pending");
    setTyped({});
    setTypedRes({ state: "idle" });
    setFinalLabels(null);
    setDraft({ state: "idle" });
  }

  /* station 2: measure */
  async function runMeasure(kind: "upload" | "fixture", fixtureId?: string) {
    resetAfterClip();
    setMeasure({ state: "busy", t0: Date.now() });
    let body: Record<string, unknown>;
    if (kind === "upload" && file) {
      let dataUrl: string;
      try {
        dataUrl = await readDataUrl(file);
      } catch {
        return setMeasure({ state: "error", err: { reason: "PAYLOAD", detail: "the browser could not read that file; try exporting it again as MP4" } });
      }
      body = { upload: dataUrl, judge_code: judgeCode.trim(), fps: fpsNum, frames: nFrames, scale: MARK_SYSTEMS[system].scale, run_id: runId.current };
    } else {
      body = { fixture: fixtureId, run_id: runId.current };
    }
    const r = await api<MeasureResp>("measure", body);
    if (!r.ok) return setMeasure({ state: "error", err: { reason: r.reason, detail: r.detail } });
    pushUsage(r.data.usage);
    if (kind === "fixture" && r.data.clip.file) setVideoUrl(r.data.clip.file);
    setFrameIdx(r.data.geometry.label_frames?.[0] ?? 0);
    setMeasure({ state: "done", data: r.data, ms: r.ms });
  }

  const geom = measure.state === "done" ? measure.data.geometry : null;
  const geomFps = geom?.fps ?? fpsNum ?? 1;

  // keep the video on the frame the overlay draws
  useEffect(() => {
    const v = videoRef.current;
    if (v && geom) void seek(v, (frameIdx + 0.5) / geomFps);
  }, [frameIdx, geom, geomFps]);

  /* station 3: labels */
  async function grabFrames(idx: number[]): Promise<Record<number, string>> {
    const v = videoRef.current;
    if (!v) return {};
    const c = document.createElement("canvas");
    c.width = v.videoWidth;
    c.height = v.videoHeight;
    const ctx = c.getContext("2d");
    const out: Record<number, string> = {};
    for (const i of idx) {
      await seek(v, (i + 0.5) / geomFps);
      ctx?.drawImage(v, 0, 0, c.width, c.height);
      out[i] = c.toDataURL("image/jpeg", 0.92);
    }
    await seek(v, (frameIdx + 0.5) / geomFps);
    return out;
  }

  async function runLabels() {
    if (!geom?.label_frames) return;
    setLabels({ state: "busy", t0: Date.now() });
    setAnchor("pending");
    setFinalLabels(null);
    setDraft({ state: "idle" });
    const shots = await grabFrames(geom.label_frames);
    setFrameShots(shots);
    const r = await api<Labels>("labels", { geometry: geom, frames: shots, run_id: runId.current });
    if (!r.ok) return setLabels({ state: "error", err: { reason: r.reason, detail: r.detail } });
    pushUsage(r.data.usage);
    setLabels({ state: "done", data: r.data, ms: r.ms });
    if (!r.data.checks.ok) setAnchor("rejected");
  }

  async function runTyped() {
    if (!geom) return;
    setTypedRes({ state: "busy", t0: Date.now() });
    const clean = Object.fromEntries(Object.entries(typed).filter(([, v]) => v.trim() !== "").map(([k, v]) => [k, v.trim()]));
    const r = await api<Labels>("labels", { geometry: geom, typed: clean, frame: geom.label_frames?.[0], run_id: runId.current });
    if (!r.ok) return setTypedRes({ state: "error", err: { reason: r.reason, detail: r.detail } });
    setTypedRes({ state: "done", data: r.data, ms: r.ms });
    if (r.data.checks.ok) void acceptLabels(r.data); // failing typed values stay editable with their ticks shown
  }

  /* station 4: draft (code only), then station 5: program */
  async function acceptLabels(l: Labels) {
    if (!geom) return;
    setFinalLabels(l);
    setDraft({ state: "busy", t0: Date.now() });
    const r = await api<DraftResp>("draft", { geometry: geom, drafts: l.drafts });
    if (!r.ok) return setDraft({ state: "error", err: { reason: r.reason, detail: r.detail } });
    setDraft({ state: "done", data: r.data, ms: r.ms });
    if (program.state !== "done") {
      setProgram({ state: "busy", t0: Date.now() });
      const p = await api<ProgramResp>("program");
      setProgram(p.ok ? { state: "done", data: p.data, ms: p.ms } : { state: "error", err: { reason: p.reason, detail: p.detail } });
    }
  }

  const mode: "ship" | "barge" = (geom?.mark_system.scale ?? MARK_SYSTEMS[system].scale) < 1 ? "barge" : "ship";
  const labelFrame = geom?.label_frames ? geom.frames.find((f) => f.i === geom.label_frames![0]) : undefined;
  const shownFrame = geom?.frames.find((f) => f.i === frameIdx);
  const draftData = draft.state === "done" ? draft.data : null;
  const fit = draftData?.frames.find((f) => f.i === frameIdx);
  const labelsData = labels.state === "done" ? labels.data : null;
  const fixtures = health.state === "done" ? health.data.fixtures : [];

  return (
    <div className="flow">
      <Station n={1} title="Clip" open done={measure.state === "done"}>
        <div className="grid2">
          <div>
            <h3 className="h4">Our fixture clip</h3>
            {health.state === "busy" ? <p className="muted">Checking the live API…</p> : null}
            {health.state === "error" ? (
              <div className="error-box" role="alert">
                <p>
                  <span className="data error-box__code">{health.err.reason}</span> the live API did not answer ({health.err.detail}).
                </p>
                <p className="small">
                  Live stations need it; the recorded runs do not. <Link href="/">Open the recorded runs →</Link>
                </p>
              </div>
            ) : null}
            {health.state === "done" && fixtures.length === 0 ? (
              <p>
                No live fixture clip is registered on this deployment yet; until then, <Link href="/">open the recorded runs</Link>.
              </p>
            ) : null}
            {fixtures.length ? (
              <ul className="fixture-list">
                {fixtures.map((f) => (
                  <li key={f}>
                    <button
                      type="button"
                      className="btn"
                      disabled={measure.state === "busy"}
                      onClick={() => {
                        setFixture(f);
                        setFile(null);
                        void runMeasure("fixture", f);
                      }}
                    >
                      Run live on <span className="data">{f}</span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
            {health.state === "done" && health.data.budget ? (
              <p className="small error-inline">
                <span className="data">BUDGET</span> {health.data.budget}
              </p>
            ) : null}
          </div>
          <div>
            <h3 className="h4">Upload a prepared clip (judge code)</h3>
            <div className="guidance small">
              <p>
                <strong>Supported marks:</strong> {MARK_SYSTEMS.ship.label.toLowerCase()} (white numerals, whole metres with
                “M”), or the {MARK_SYSTEMS.barge.label}.
              </p>
              <p>
                <strong>Camera:</strong> side-on to the hull, held still, the mark column and the waterline both in frame,
                cropped close to the marks. On iPhone, export or share the clip as MP4 first (Most Compatible). Prepared MP4 only: at most {MAX_SECONDS} s, {MAX_FPS} fps and{" "}
                {MAX_BYTES / 1048576} MB.
              </p>
            </div>
            <fieldset className="field">
              <legend>Mark system</legend>
              {(Object.keys(MARK_SYSTEMS) as MarkSystemId[]).map((k) => (
                <label key={k} className="radio">
                  <input type="radio" name="marks" value={k} checked={system === k} onChange={() => setSystem(k)} />{" "}
                  {MARK_SYSTEMS[k].label} <span className="muted data">(scale {MARK_SYSTEMS[k].scale})</span>
                </label>
              ))}
            </fieldset>
            <label className="field">
              <span>MP4 clip</span>
              <input
                type="file"
                accept="video/mp4"
                capture="environment"
                onChange={(e) => {
                  setFixture(null);
                  setMeta(null);
                  resetAfterClip();
                  setFile(e.target.files?.[0] ?? null);
                }}
              />
            </label>
            <div className="field-row">
              <label className="field">
                <span>Frame rate of the clip (fps)</span>
                <input type="number" inputMode="decimal" min={1} max={MAX_FPS} step={1} value={fps} onChange={(e) => setFps(e.target.value)} />
              </label>
              <label className="field">
                <span>Judge code</span>
                <input type="password" autoComplete="off" value={judgeCode} onChange={(e) => setJudgeCode(e.target.value)} />
              </label>
            </div>
            {file ? (
              <p className="small data">
                {file.name} · {(file.size / 1048576).toFixed(2)} MB
                {meta ? ` · ${meta.dur.toFixed(2)} s · ${meta.w}×${meta.h} px · ${nFrames} frames` : " · reading…"}
              </p>
            ) : null}
            {clipProblems.length ? (
              <ul className="problems small">
                {clipProblems.map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
            ) : null}
            <button
              type="button"
              className="btn btn--accent"
              disabled={!file || !meta || clipProblems.length > 0 || measure.state === "busy"}
              onClick={() => void runMeasure("upload")}
            >
              Measure this clip (SAM 3.1)
            </button>
          </div>
        </div>
      </Station>

      <Station n={2} title="Measure" open={measure.state !== "idle" || !!videoUrl} done={draft.state === "done"} live>
        {measure.state === "busy" ? (
          <p>
            SAM 3.1 is tracking the numerals and the water (usually 30–45 s)… <Elapsed t0={measure.t0} />
          </p>
        ) : null}
        {measure.state === "error" ? <ErrorBox err={measure.err} /> : null}
        {geom?.row1 ? (
          <div className="refusal" role="alert">
            <span className="refusal__word">REFUSE</span> <span className="data">{geom.row1}</span>
            <span className="small">
              {" "}
              — {measure.state === "done" && measure.data.row1_hint ? measure.data.row1_hint : "the row-1 check stopped this clip before labels."}{" "}
              The overlay below stays visible.
            </span>
          </div>
        ) : null}
        <div className="grid2">
          <div className="stage" style={meta ? { aspectRatio: `${meta.w} / ${meta.h}` } : undefined}>
            {videoUrl ? (
              <video
                ref={videoRef}
                src={videoUrl}
                muted
                playsInline
                preload="auto"
                onLoadedMetadata={(e) => {
                  const v = e.currentTarget;
                  setMeta({ w: v.videoWidth, h: v.videoHeight, dur: v.duration });
                }}
              />
            ) : null}
            {geom && shownFrame && meta ? (
              <Overlay
                frame={shownFrame}
                column={geom.column}
                fit={fit}
                labels={finalLabels?.checks.labels}
                drafts={finalLabels?.drafts}
                size={{ w: meta.w, h: meta.h }}
              />
            ) : null}
          </div>
          {geom ? (
            <div>
              <label className="field">
                <span>
                  Frame <span className="data">{frameIdx}</span> / <span className="data">{geom.n_frames - 1}</span>
                </span>
                <input type="range" min={0} max={geom.n_frames - 1} value={frameIdx} onChange={(e) => setFrameIdx(Number(e.target.value))} />
              </label>
              <dl className="kv">
                <div>
                  <dt>Frames</dt>
                  <dd className="data">
                    {geom.n_frames} at {geom.fps} fps
                  </dd>
                </div>
                <div>
                  <dt>Numeral objects · water objects</dt>
                  <dd className="data">
                    {geom.raw_numeral_objs ?? DASH} · {geom.raw_water_objs ?? DASH}
                  </dd>
                </div>
                <div>
                  <dt>Frames with ≥ 3 tokens · with water</dt>
                  <dd className="data">
                    {geom.frames_with_3_tokens ?? DASH} · {geom.frames_with_water ?? DASH}
                  </dd>
                </div>
                <div>
                  <dt>Mark system</dt>
                  <dd className="data">
                    {geom.mark_system.id} · scale {geom.mark_system.scale}
                  </dd>
                </div>
                <div>
                  <dt>Label frames</dt>
                  <dd className="data">{geom.label_frames ? geom.label_frames.join(" · ") : DASH}</dd>
                </div>
                {measure.state === "done" ? (
                  <div>
                    <dt>Round trip</dt>
                    <dd className="data">{fx(measure.ms / 1000, 1)} s</dd>
                  </div>
                ) : null}
              </dl>
            </div>
          ) : null}
        </div>
      </Station>

      <Station n={3} title="Labels" open={!!geom && !geom.row1 && !!geom.label_frames} done={!!finalLabels} live>
        {labels.state === "idle" ? (
          <button type="button" className="btn btn--accent" onClick={() => void runLabels()}>
            Read the mark labels (Muse Spark 1.3)
          </button>
        ) : null}
        {labels.state === "busy" ? (
          <p>
            Spark 1.3 is reading two frames… <Elapsed t0={labels.t0} />
          </p>
        ) : null}
        {labels.state === "error" ? (
          <>
            <ErrorBox err={labels.err} />
            <button type="button" className="btn" onClick={() => setAnchor("rejected")}>
              Type the labels by hand instead
            </button>
          </>
        ) : null}
        {labelsData ? (
          <>
            <LabelChecks reads={labelsData.reads} checks={labelsData.checks} drafts={labelsData.drafts} readBy="muse-spark-1.3" />
            {labelsData.checks.ok ? (
              <div className="anchor">
                <h3 className="h4">Confirm the anchor</h3>
                <ul className="anchor__list">
                  {(labelsData.checks.anchor_tokens ?? []).map((t) => (
                    <li key={t}>
                      <AnchorCrop shot={geom?.label_frames ? frameShots[geom.label_frames[0]] : undefined} frame={labelFrame} track={t} />
                      <span>
                        Spark reads <span className="mark-label">{labelsData.checks.labels?.[t] ?? DASH}</span> on token{" "}
                        <span className="data">{t}</span>
                      </span>
                    </li>
                  ))}
                </ul>
                {anchor === "pending" ? (
                  <div className="btn-row">
                    <button
                      type="button"
                      className="btn btn--accent"
                      onClick={() => {
                        setAnchor("confirmed");
                        void acceptLabels(labelsData);
                      }}
                    >
                      Confirm — that is what is painted
                    </button>
                    <button type="button" className="btn" onClick={() => setAnchor("rejected")}>
                      Reject — type the labels
                    </button>
                  </div>
                ) : (
                  <p className="small muted">Anchor {anchor}.</p>
                )}
              </div>
            ) : (
              <p className="error-inline">The reads failed the code checks after a re-read: type the values by hand.</p>
            )}
          </>
        ) : null}
        {anchor === "rejected" && labelFrame ? (
          <div className="typed">
            <h3 className="h4">
              Type the labels <Badge tone="degraded">degraded: labels by hand</Badge>
            </h3>
            <p className="small muted">
              One field per mark token in frame <span className="data">{labelFrame.i}</span>, as painted (e.g. a digit, or a
              whole metre with M).
            </p>
            <div className="typed__grid">
              {[...labelFrame.tokens]
                .sort((a, b) => b.bottom - a.bottom)
                .map((t) => (
                  <label key={t.track} className="field field--token">
                    <AnchorCrop shot={geom?.label_frames ? frameShots[geom.label_frames[0]] : undefined} frame={labelFrame} track={t.track} />
                    <span className="data">{t.track}</span>
                    <input
                      type="text"
                      value={typed[t.track] ?? ""}
                      placeholder={labelsData?.checks.labels?.[t.track] ?? ""}
                      onChange={(e) => setTyped((s) => ({ ...s, [t.track]: e.target.value }))}
                    />
                  </label>
                ))}
            </div>
            <button type="button" className="btn btn--accent" disabled={typedRes.state === "busy"} onClick={() => void runTyped()}>
              Check the typed labels (code only)
            </button>
            {typedRes.state === "error" ? <ErrorBox err={typedRes.err} /> : null}
            {typedRes.state === "done" ? (
              <LabelChecks checks={typedRes.data.checks} drafts={typedRes.data.drafts} typed />
            ) : null}
          </div>
        ) : null}
      </Station>

      <Station n={4} title="Draft" open={draft.state !== "idle"} done={draft.state === "done"} live>
        {draft.state === "busy" ? <p>Averaging the waterline over the frames…</p> : null}
        {draft.state === "error" ? <ErrorBox err={draft.err} /> : null}
        {draftData ? (
          <div className="mrun__grid">
            <div className="mrun__data">
              <WaveChart id="live" frames={draftData.frames} result={draftData.result} markScale={geom?.mark_system.scale ?? 1} />
            </div>
            <ResultCard result={draftData.result} noTruth={mode === "ship"} />
          </div>
        ) : null}
        {finalLabels?.typed ? <Badge tone="degraded">degraded: labels by hand</Badge> : null}
      </Station>

      <Station n={5} title="Program" open={program.state !== "idle" && mode === "ship"} done={program.state === "done"} live note={mode === "barge" ? "Barge mode uses the analytic box geometry: no model-written program." : undefined}>
        {program.state === "busy" ? <p>Loading the cached proven program…</p> : null}
        {program.state === "error" ? <ErrorBox err={program.err} /> : null}
        {program.state === "done" ? (
          <>
            <p className="small muted">
              The cached program that passed its booklet self-test (run <span className="data">{program.data.run ?? DASH}</span>
              ). Regeneration is not offered here.
            </p>
            <ProgramProof program={program.data} selftest={program.data.selftest} live />
          </>
        ) : null}
      </Station>

      <Station
        n={6}
        title="Survey + certificate"
        open={!!draftData && (mode === "barge" || program.state === "done")}
        live
      >
        {draftData && geom && finalLabels ? (
          <SurveyStation
            mode={mode}
            runId={runId.current}
            geom={geom}
            draft={draftData}
            labels={finalLabels}
            clip={measure.state === "done" ? measure.data.clip : { id: fixture ?? "upload" }}
            usage={usage}
            anchorConfirmed={anchor === "confirmed" ? true : anchor === "rejected" ? false : null}
          />
        ) : null}
      </Station>

      <div className="flow__strip">
        <ModelStrip rows={usage} label="Model calls this session" />
      </div>
    </div>
  );
}

/** Crop of one token box from a grabbed frame, so the anchor read sits beside the painted glyphs. */
function AnchorCrop({ shot, frame, track }: { shot?: string; frame?: { tokens: { track: string; box: [number, number, number, number] }[] }; track: string }) {
  const [src, setSrc] = useState<string | null>(null);
  useEffect(() => {
    const tok = frame?.tokens.find((t) => t.track === track);
    if (!shot || !tok) return;
    const img = new Image();
    img.onload = () => {
      const [x0, y0, x1, y1] = tok.box;
      const pad = Math.max(4, (y1 - y0) * 0.3);
      const sx = Math.max(0, x0 - pad);
      const sy = Math.max(0, y0 - pad);
      const sw = Math.min(img.width - sx, x1 - x0 + 2 * pad);
      const sh = Math.min(img.height - sy, y1 - y0 + 2 * pad);
      const c = document.createElement("canvas");
      c.width = Math.max(1, Math.round(sw * 2));
      c.height = Math.max(1, Math.round(sh * 2));
      c.getContext("2d")?.drawImage(img, sx, sy, sw, sh, 0, 0, c.width, c.height);
      setSrc(c.toDataURL("image/jpeg", 0.9));
    };
    img.src = shot;
  }, [shot, frame, track]);
  return src ? <img className="crop" src={src} alt={`Crop of token ${track}`} /> : <span className="crop crop--empty" aria-hidden="true" />;
}

/* ---------- station 6 ---------- */

/** The clip measures the midship marks; the other four positions are entered by the surveyor. */
const SOURCES = Object.fromEntries(POSITIONS.map((p) => [p, p.startsWith("mid") ? "live" : "entered"])) as Record<
  Position,
  "live" | "entered"
>;

function SurveyStation({
  mode,
  runId,
  geom,
  draft,
  labels,
  clip,
  usage,
  anchorConfirmed,
}: {
  anchorConfirmed: boolean | null;
  mode: "ship" | "barge";
  runId: string;
  geom: Geometry;
  draft: DraftResp;
  labels: Labels;
  clip: ClipInfo;
  usage: UsageRow[];
}) {
  const d = draft.result.d_m;
  const liveDraft = isNum(d) ? d.toFixed(3) : "";
  const [drafts, setDrafts] = useState<Record<Position, string>>(() =>
    Object.fromEntries(POSITIONS.map((p) => [p, liveDraft])) as Record<Position, string>,
  );
  const sources = SOURCES;
  const [sg, setSg] = useState(SHIP_SG.init);
  const [ded, setDed] = useState({ ballast: "", fw: "", fuel: "", other: "" });
  const [lightship, setLightship] = useState("");
  const [initialNet, setInitialNet] = useState("");
  const [bl, setBl] = useState("");
  const [tol, setTol] = useState("");
  const [whatIfOn, setWhatIfOn] = useState(false);
  const [whatIf, setWhatIf] = useState<number | null>(null);
  const [res, setRes] = useState<Async<{ certificate: Certificate }>>({ state: "idle" });
  const seq = useRef(0);

  const body = useMemo(() => {
    const measure = { ...draft.result, row1: geom.row1 };
    const models = Array.from(new Set(usage.map((u) => u.model)));
    const common = {
      run_mode: "LIVE",
      run_id: runId,
      measure,
      labels: { ...labels, anchor_confirmed: labels.typed ? null : anchorConfirmed },
      models,
      clip: { id: clip.id, source: clip.source ?? "upload" },
    };
    if (mode === "barge") {
      return { ...common, mode, what_if: whatIfOn && whatIf != null ? { rho_kg_m3: whatIf * 1000 } : null };
    }
    if (!isNum(d)) return { ...common, mode, survey: null }; // measurement refused: the certificate says why
    const dd = Object.fromEntries(POSITIONS.map((p) => [p, num(drafts[p])]));
    if (Object.values(dd).some((v) => v === undefined)) return null;
    const deductibles = Object.fromEntries(Object.entries(ded).filter(([, v]) => num(v) !== undefined).map(([k, v]) => [k, num(v)]));
    return {
      ...common,
      mode,
      survey: {
        drafts: dd,
        sources,
        u_live_m: draft.result.u_rep_m,
        sg,
        deductibles,
        ...(num(lightship) !== undefined ? { lightship_constant: num(lightship) } : {}),
        ...(num(initialNet) !== undefined ? { initial_net: num(initialNet) } : {}),
      },
      ...(num(bl) !== undefined ? { bl: num(bl) } : {}),
      ...(num(tol) !== undefined ? { tol_pct: num(tol) } : {}),
    };
  }, [mode, runId, draft, d, geom.row1, labels, anchorConfirmed, usage, clip, drafts, sg, ded, lightship, initialNet, bl, tol, whatIfOn, whatIf]);

  // debounced re-POST: every input (density included) moves every number
  useEffect(() => {
    if (!body) return;
    const my = ++seq.current;
    const t = setTimeout(async () => {
      setRes((r) => (r.state === "done" ? r : { state: "busy", t0: Date.now() }));
      const r = await api<{ certificate: Certificate }>("survey", body);
      if (my !== seq.current) return;
      setRes(r.ok ? { state: "done", data: r.data, ms: r.ms } : { state: "error", err: { reason: r.reason, detail: r.detail } });
    }, 400);
    return () => clearTimeout(t);
  }, [body]);

  const cert = res.state === "done" ? res.data.certificate : null;
  const recordedRho = cert?.survey?.barge?.rho_kg_m3;
  useEffect(() => {
    if (whatIf == null && isNum(recordedRho) && !whatIfOn) setWhatIf(recordedRho / 1000);
  }, [recordedRho, whatIf, whatIfOn]);

  function openPrintable() {
    if (!cert) return;
    const run: Run = {
      run_id: cert.run_id,
      kind: "live",
      title: `Live run ${cert.run_id}`,
      date: cert.created_at,
      clip,
      geometry: { ...geom, frames: [] },
      labels,
      draft: { result: draft.result, frames: draft.frames },
      certificate: cert,
      usage,
    };
    try {
      window.localStorage.setItem(LOCAL_RUN_KEY, JSON.stringify(run));
      window.open("/certificate?run=local", "_blank", "noopener");
    } catch {
      /* storage full or blocked: the preview below stays the record */
    }
  }

  return (
    <div className="grid2 grid2--survey">
      <div>
        {mode === "ship" ? (
          <>
            <h3 className="h4">Draft sheet</h3>
            <div className="sheet">
              {POSITIONS.map((p) => (
                <label key={p} className="field field--sheet">
                  <span>
                    {POSITION_LABEL[p]}{" "}
                    <span className={sources[p] === "live" ? "src src--live" : "src"}>{sources[p]}</span>
                  </span>
                  <input
                    type="number"
                    inputMode="decimal"
                    step="0.001"
                    value={drafts[p]}
                    readOnly={sources[p] === "live"}
                    aria-readonly={sources[p] === "live"}
                    onChange={(e) => setDrafts((s) => ({ ...s, [p]: e.target.value }))}
                  />
                </label>
              ))}
            </div>
            <label className="field">
              <span>
                Dock density <span className="data">{sg.toFixed(3)} t/m³</span>
              </span>
              <input type="range" min={SHIP_SG.min} max={SHIP_SG.max} step={SHIP_SG.step} value={sg} onChange={(e) => setSg(Number(e.target.value))} />
            </label>
            <fieldset className="field">
              <legend>Deductibles (t)</legend>
              <div className="field-row field-row--4">
                {(Object.keys(ded) as (keyof typeof ded)[]).map((k) => (
                  <label key={k} className="field">
                    <span>{k}</span>
                    <input type="number" inputMode="decimal" value={ded[k]} onChange={(e) => setDed((s) => ({ ...s, [k]: e.target.value }))} />
                  </label>
                ))}
              </div>
            </fieldset>
            <div className="field-row">
              <label className="field">
                <span>Lightship + constant (t, optional)</span>
                <input type="number" inputMode="decimal" value={lightship} onChange={(e) => setLightship(e.target.value)} />
              </label>
              <label className="field">
                <span>Initial net (t, optional)</span>
                <input type="number" inputMode="decimal" value={initialNet} onChange={(e) => setInitialNet(e.target.value)} />
              </label>
            </div>
            <div className="field-row">
              <label className="field">
                <span>B/L figure (t)</span>
                <input type="number" inputMode="decimal" value={bl} onChange={(e) => setBl(e.target.value)} />
              </label>
              <label className="field">
                <span>Tolerance %</span>
                <input type="number" inputMode="decimal" value={tol} onChange={(e) => setTol(e.target.value)} />
              </label>
            </div>
          </>
        ) : (
          <>
            <h3 className="h4">Barge geometry (locked)</h3>
            {cert?.survey?.barge ? (
              <dl className="kv">
                <div>
                  <dt>L · B</dt>
                  <dd className="data">
                    {fx(cert.survey.barge.L_m, 3)} m · {fx(cert.survey.barge.B_m, 3)} m
                  </dd>
                </div>
                <div>
                  <dt>Light weight</dt>
                  <dd className="data">{fx(cert.survey.barge.light_kg, 3)} kg</dd>
                </div>
                <div>
                  <dt>Zero offset</dt>
                  <dd className="data">{fx(cert.survey.barge.zero_offset_m, 4)} m</dd>
                </div>
              </dl>
            ) : null}
            {cert?.survey?.booklet_note ? <p className="small muted">{cert.survey.booklet_note}</p> : null}
            <label className="field">
              <span>
                Water density (recorded){" "}
                <span className="data">{isNum(recordedRho) ? `${(recordedRho / 1000).toFixed(4)} t/m³` : DASH}</span>
              </span>
              <input type="range" disabled min={BARGE_WHAT_IF_SG.min} max={BARGE_WHAT_IF_SG.max} step={BARGE_WHAT_IF_SG.step} value={isNum(recordedRho) ? recordedRho / 1000 : BARGE_WHAT_IF_SG.min} readOnly />
            </label>
            <fieldset className="field whatif">
              <legend>What-if (stamps NOT SCORED)</legend>
              <label className="radio">
                <input type="checkbox" checked={whatIfOn} onChange={(e) => setWhatIfOn(e.target.checked)} /> Move the density off the
                recorded value
              </label>
              <label className="field">
                <span>
                  What-if density <span className="data">{whatIf != null ? `${whatIf.toFixed(4)} t/m³` : DASH}</span>
                </span>
                <input
                  type="range"
                  disabled={!whatIfOn}
                  min={BARGE_WHAT_IF_SG.min}
                  max={BARGE_WHAT_IF_SG.max}
                  step={BARGE_WHAT_IF_SG.step}
                  value={whatIf ?? BARGE_WHAT_IF_SG.min}
                  onChange={(e) => setWhatIf(Number(e.target.value))}
                />
              </label>
            </fieldset>
          </>
        )}
      </div>
      <div>
        <h3 className="h4">
          Certificate preview {res.state === "busy" ? <span className="muted small">updating…</span> : null}
        </h3>
        {mode === "ship" && !body ? <p className="error-inline small">Every position needs a draft.</p> : null}
        {res.state === "error" ? <ErrorBox err={res.err} /> : null}
        {cert ? (
          <>
            <DecisionStamp decision={cert.decision} reason={cert.reason} hint={cert.hint} warnings={cert.warnings} row={cert.decision_row} />
            {cert.survey ? <SurveyResult survey={cert.survey} booklet={cert.booklet} /> : null}
            <p className="small muted data">
              {cert.run_id} · {cert.mode} · proof: {cert.proof}
            </p>
            <button type="button" className="btn btn--accent" onClick={openPrintable}>
              Open printable certificate
            </button>
          </>
        ) : null}
      </div>
    </div>
  );
}
