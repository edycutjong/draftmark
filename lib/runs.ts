/** Server-only loaders for the committed recorded runs (public/runs). Used at build time (static pages). */
import fs from "node:fs";
import path from "node:path";
import type { IndexEntry, Run } from "./types";

const DIR = path.join(process.cwd(), "public", "runs");

export function runIndex(): IndexEntry[] {
  return (JSON.parse(fs.readFileSync(path.join(DIR, "index.json"), "utf8")) as { runs: IndexEntry[] }).runs;
}

export function loadRun(runId: string): Run | null {
  if (!runIndex().some((r) => r.run_id === runId)) return null;
  return JSON.parse(fs.readFileSync(path.join(DIR, `${runId}.json`), "utf8")) as Run;
}

/** Keep the one frame the overlay draws; drop the rest of the per-frame geometry from the page payload. */
export function slimForPage(run: Run): Run {
  if (!run.geometry) return run;
  const g = run.geometry;
  const pick = g.label_frames?.[0] ?? g.frames.find((f) => f.tokens.length)?.i ?? 0;
  return { ...run, geometry: { ...g, frames: g.frames.filter((f) => f.i === pick) } };
}
