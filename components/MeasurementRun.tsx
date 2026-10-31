import Link from "next/link";
import type { Run } from "@/lib/types";
import { Badge, Badges } from "./Badge";
import { Overlay } from "./Overlay";
import { WaveChart } from "./WaveChart";
import { ResultCard } from "./ResultCard";
import { LabelChecks } from "./LabelChecks";
import { DecisionStamp } from "./DecisionStamp";
import { ModelStrip } from "./ModelStrip";

/** One recorded measurement run: overlay schematic, wave chart, result, labels, certificate stamp. */
export function MeasurementRun({ run }: { run: Run }) {
  const g = run.geometry;
  const frame = g?.frames[0];
  const fit = frame ? run.draft?.frames.find((f) => f.i === frame.i) : undefined;
  const c = run.certificate;
  const real = run.kind === "public-clip";
  const day = run.date.split(" ")[0];
  return (
    <div className="mrun">
      <Badges>
        {real ? (
          <>
            <Badge tone="recorded">RECORDED · {day} · real API calls</Badge>
            <Badge tone="caveat">third-party test clip · no ground truth · frames not re-hosted</Badge>
            {c.clip?.source?.startsWith("http") ? (
              <a className="badge badge--link" href={c.clip.source} rel="noopener noreferrer" target="_blank">
                source video (YouTube) ↗
              </a>
            ) : null}
          </>
        ) : (
          <Badge tone="synthetic">SYNTHETIC geometry — not SAM, not the kitchen scale</Badge>
        )}
      </Badges>
      <h3 className="h3">{run.title}</h3>

      <div className="mrun__grid">
        <figure className="mrun__overlay">
          {frame && g ? (
            <Overlay
              frame={frame}
              column={g.column}
              fit={fit}
              labels={run.labels?.checks.labels}
              drafts={run.labels?.drafts}
              title={`Schematic of frame ${frame.i}: mark boxes, water surface and fitted draft scale, drawn from the geometry`}
            />
          ) : null}
          <figcaption className="small muted">
            Frame <span className="data">{frame?.i}</span> of <span className="data">{g?.n_frames}</span> at{" "}
            <span className="data">{g?.fps}</span> fps · schematic from the geometry JSON, no video pixels
          </figcaption>
        </figure>
        <div className="mrun__data">
          {run.draft ? (
            <WaveChart
              id={run.run_id}
              frames={run.draft.frames}
              result={run.draft.result}
              markScale={g?.mark_system.scale ?? 1}
            />
          ) : null}
          {run.draft ? <ResultCard result={run.draft.result} noTruth={real} /> : null}
        </div>
      </div>

      <div className="mrun__grid mrun__grid--even">
        <div>
          <h4 className="h4">Mark labels</h4>
          {run.labels ? (
            <LabelChecks
              reads={run.labels.reads}
              checks={run.labels.checks}
              drafts={run.labels.drafts}
              readBy={c.labels?.read_by}
              synthetic={run.labels.synthetic}
              typed={run.labels.typed}
            />
          ) : null}
        </div>
        <div>
          <h4 className="h4">Certificate decision</h4>
          <DecisionStamp decision={c.decision} reason={c.reason} hint={c.hint} warnings={c.warnings} row={c.decision_row} />
          <p className="small">
            <Link href={`/certificate/${run.run_id}`}>Open the printable certificate →</Link>
          </p>
        </div>
      </div>
      <ModelStrip rows={run.usage ?? []} />
    </div>
  );
}
