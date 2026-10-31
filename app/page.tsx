import Link from "next/link";
import { loadRun, runIndex, slimForPage } from "@/lib/runs";
import type { Run } from "@/lib/types";
import { SiteHeader, Waterline } from "@/components/SiteChrome";
import { MarkColumn } from "@/components/MarkColumn";
import { Tabs } from "@/components/Tabs";
import { MeasurementRun } from "@/components/MeasurementRun";
import { ProgramProof } from "@/components/ProgramProof";
import { DecisionStamp } from "@/components/DecisionStamp";
import { SurveyResult } from "@/components/SurveyResult";
import { ModelStrip } from "@/components/ModelStrip";
import { Badge, Badges } from "@/components/Badge";

export const dynamic = "force-static";

export default function Home() {
  const index = runIndex();
  const measurement = index
    .filter((e) => e.kind === "public-clip" || e.kind === "synthetic")
    .sort((a, b) => (a.kind === b.kind ? 0 : a.kind === "public-clip" ? -1 : 1))
    .map((e) => loadRun(e.run_id))
    .filter((r): r is Run => r !== null)
    .map(slimForPage);
  const programEntry = index.find((e) => e.kind === "booklet-proof");
  const programRun = programEntry ? loadRun(programEntry.run_id) : null;

  const hero = measurement.find((r) => r.kind === "public-clip");
  const heroMarks = hero?.labels
    ? Object.entries(hero.labels.checks.labels ?? {}).map(([t, label]) => ({ label, draft: hero.labels!.drafts[t] }))
    : [];

  return (
    <>
      <SiteHeader />
      <main className="page">
        <section className="hero">
          <div className="hero__text">
            <p className="eyebrow">Recorded runs · real API calls · every number printed by code</p>
            <h1 className="hero__title">Weigh a ship&apos;s cargo from a phone video of its draft marks.</h1>
            <p className="lede">
              SAM 3.1 tracks the painted draft numerals and the water surface in every frame; code averages the
              waterline through the swell into one draft with a stated uncertainty. Muse Spark 1.3 reads the mark
              labels and five code checks confirm them. Muse Wonder 1.0 wrote the survey program from a stability
              booklet, and that program had to reproduce the booklet&apos;s printed conditions before it may compute.
            </p>
            <p>
              <Link href="/survey" className="btn btn--accent">
                Run it live →
              </Link>
            </p>
          </div>
          {hero ? (
            <div className="hero__motif">
              <MarkColumn marks={heroMarks} d={hero.draft?.result.d_m ?? null} u={hero.draft?.result.u_rep_m ?? null} />
              <p className="small muted">
                Marks as read on <span className="data">{hero.clip?.id}</span>; the line is its wave-averaged draft.
              </p>
            </div>
          ) : null}
        </section>

        <aside className="honesty" aria-label="What these runs do and do not prove">
          <h2 className="h4">What is and is not proven here</h2>
          <ul>
            <li>
              <strong>SYNTHETIC barge:</strong> weight accuracy is checked only against a code-rendered barge whose truth is
              known by construction. No physical scale check has been done.
            </li>
            <li>
              <strong>Real hulls:</strong> the two clips are third-party test footage with no ground truth. They show the
              measurement and an honest refusal, not a weight.
            </li>
            <li>
              <strong>Trieste booklet:</strong> a Ro-Ro/passenger ship, not a bulk carrier. It proves that Wonder&apos;s program
              reproduces the booklet&apos;s printed conditions.
            </li>
            <li>
              <strong>Prototype:</strong> not a surveyor&apos;s certificate.
            </li>
          </ul>
        </aside>

        <section className="proof-section" aria-labelledby="measurement-h">
          <div className="section-head">
            <p className="eyebrow">Proof 1 of 2</p>
            <h2 id="measurement-h" className="h2">
              Measurement: video → draft
            </h2>
            <p className="muted">
              Does the clip give a stable, honest draft? Real hull clips have no ground truth, so only repeatability is
              stated; the synthetic barge checks the arithmetic against known geometry.
            </p>
          </div>
          <Tabs
            label="Measurement runs"
            tabs={measurement.map((r) => ({
              id: r.run_id,
              label: (
                <>
                  <span className="data">{r.clip?.id ?? r.run_id}</span>
                  <span className="tab__sub">{r.kind === "synthetic" ? "synthetic" : "real hull clip"}</span>
                </>
              ),
            }))}
          >
            {measurement.map((r) => (
              <MeasurementRun key={r.run_id} run={r} />
            ))}
          </Tabs>
        </section>

        <Waterline label="Two proofs — never merged" />

        {programRun?.program && programRun.selftest ? (
          <section className="proof-section" aria-labelledby="program-h">
            <div className="section-head">
              <p className="eyebrow">Proof 2 of 2</p>
              <h2 id="program-h" className="h2">
                Program: booklet → survey program
              </h2>
              <Badges>
                <Badge tone="recorded">RECORDED · {programRun.date.split(" ")[0]}</Badge>
                <Badge tone="proof">no scale truth</Badge>
              </Badges>
              <p className="muted">{programRun.title}</p>
            </div>
            <ProgramProof
              program={programRun.program}
              selftest={{ ...programRun.selftest, rows: programRun.selftest.rows.map((r) => ({ ...r, trace: undefined })) }}
            />

            <h3 className="h3">
              Survey on printed condition <span className="data">{programRun.certificate.booklet?.condition}</span>
            </h3>
            <div className="mrun__grid mrun__grid--even">
              <SurveyResult survey={programRun.certificate.survey ?? {}} booklet={programRun.certificate.booklet} />
              <div>
                <DecisionStamp
                  decision={programRun.certificate.decision}
                  reason={programRun.certificate.reason}
                  hint={programRun.certificate.hint}
                  warnings={programRun.certificate.warnings}
                  row={programRun.certificate.decision_row}
                />
                <p className="small">
                  <Link href={`/certificate/${programRun.run_id}`}>Open the printable certificate →</Link>
                </p>
              </div>
            </div>
            <ModelStrip
              rows={programRun.usage ?? []}
              attempts={programRun.program.attempts.attempts}
              attemptModel={programRun.program.meta.program_author}
              label="Program generation calls"
            />
          </section>
        ) : null}
      </main>
    </>
  );
}
