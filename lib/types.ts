/** Shapes of the recorded run JSON (public/runs/*.json) and the /api/py/* responses.
 *  Every field is optional where the producing code may omit it; components render "—" for gaps. */

export type Decision = "ISSUE" | "ISSUE_WITH_WARNING" | "REFUSE" | "PROTEST" | "NOT_SCORED";
export type RunKind = "public-clip" | "synthetic" | "booklet-proof" | "live";

export interface IndexEntry {
  run_id: string;
  kind: RunKind;
  title: string;
  date: string;
  decision: Decision;
  reason: string | null;
}

export interface Token {
  track: string;
  glyph_ids: number[];
  box: [number, number, number, number];
  bottom: number;
  n: number;
}

export interface GeomFrame {
  i: number;
  raw?: number;
  tokens: Token[];
  water: (number | null)[];
  n_water_objs?: number;
}

export interface Geometry {
  n_frames: number;
  fps: number;
  mark_system: { id: string; scale: number };
  crop?: unknown;
  column: [number, number] | null;
  frames: GeomFrame[];
  raw_numeral_objs?: number;
  raw_water_objs?: number;
  object_cap_frames?: number[];
  row1: string | null;
  label_frames: [number, number] | null;
  frames_with_3_tokens?: number;
  frames_with_water?: number;
}

export interface Checks {
  monotone?: boolean;
  pitch?: boolean;
  residual?: boolean;
  cross_frame?: boolean;
  anchor?: boolean;
  ok?: boolean;
  labels?: Record<string, string>;
  pitch_px?: number;
  resid_rms_px?: number;
  gaps_in_pitches?: number[];
  shared?: number;
  disagree?: string[];
  anchor_tokens?: string[];
  [k: string]: unknown;
}

export interface UsageRow {
  ts?: string;
  model: string;
  feature?: string;
  latency_ms?: number | null;
  est_usd?: number | null;
  tokens_in?: number | null;
  tokens_cached?: number | null;
  tokens_out?: number | null;
  frames?: number | null;
  response_id?: string | null;
  run_id?: string;
}

export interface Labels {
  ok?: boolean;
  typed?: boolean;
  synthetic?: boolean;
  drafts: Record<string, number>;
  checks: Checks;
  attempts?: number;
  reads?: Record<string, Record<string, string>>;
  response_ids?: string[];
  usage?: UsageRow[];
}

export interface DraftFrame {
  i: number;
  kept: boolean;
  drop_reason: string | null;
  n_tokens?: number;
  n_dry?: number;
  water_edge_y?: number | null;
  edge_mad?: number | null;
  pitch_px?: number | null;
  d_m?: number | null;
  a?: number | null;
  b?: number | null;
}

export interface DraftResult {
  d_m: number | null;
  u_rep_m: number | null;
  u_abs_m: number | null;
  u_parts?: { swell?: number; rand?: number; sys?: Record<string, number> };
  n_frames: number | null;
  n_kept: number | null;
  n_outliers?: number;
  n_eff: number | null;
  rho1: number | null;
  median_m?: number;
  huber_m?: number;
  sd_m?: number;
  swell_p5_p95: [number, number] | null;
  pitch_px_median?: number;
  label_shift_sensitivity_m: number | null;
  drops: Record<string, number> | null;
  refused?: boolean;
  reason?: string | null;
}

export interface Warning {
  code: string;
  hint: string;
  detail?: string;
}

export interface SurveyOut {
  program_sha?: string;
  program_author?: string;
  response_id?: string | null;
  regen_count?: number | null;
  drafts?: Record<string, number>;
  sources?: Record<string, string>;
  weights?: Record<string, number>;
  sg?: number;
  sandbox_ms?: number;
  n_cases?: number;
  out_of_table?: boolean;
  perturb_oot?: boolean;
  error?: string | null;
  trace?: Record<string, number | null>;
  disp?: number;
  t_per_mm?: Record<string, number | null>;
  u_disp?: number;
  deductibles?: Record<string, number>;
  deductions?: number;
  net?: number;
  cargo?: number | null;
  cargo_kind?: string | null;
  u_cargo?: number | null;
  u_label?: string;
  n_entered?: number;
  d_mm?: number;
  trim?: number;
  consequence?: { tpc_t_per_cm?: number; d_mm?: number; g_per_mm?: number; kg_per_mm?: number } | null;
  gate_fail?: string[];
  entered_inconsistent?: boolean;
  // barge
  barge?: { L_m: number; B_m: number; light_kg: number; zero_offset_m: number; rho_kg_m3: number };
  booklet_id?: string;
  booklet_note?: string;
  what_if?: boolean;
  light?: number;
  expected_u?: number | null;
}

export interface SelftestSummary {
  verdict: string;
  pass_count: number;
  n: number;
  probes_raised?: boolean[] | null;
  differential_n?: number | null;
  differential_max_err_pct?: number | null;
  differential_failures?: number;
  program_sha?: string;
  failed_rows?: { cond_id: string; d_mm: number; trim: number }[];
  fallback?: string | null;
}

export interface SelftestRow {
  cond_id: string;
  page: number;
  expected: number;
  got: number | null;
  err_pct: number | null;
  passed: boolean;
  first_diverging: string | null;
  error?: string | null;
  trace?: Record<string, number | null>;
}

export interface Selftest extends SelftestSummary {
  rows: SelftestRow[];
  error?: string | null;
  wall_ms?: number;
}

export interface Certificate {
  run_id: string;
  mode: "LIVE" | "RECORDED" | string;
  vessel_mode: "ship" | "barge" | string;
  proof: "booklet" | "measurement" | string;
  decision: Decision;
  reason: string | null;
  hint: string | null;
  warnings: Warning[];
  decision_row: number | null;
  draft: Partial<DraftResult> | null;
  labels: { read_by?: string; degraded?: boolean; checks?: Checks | null } | null;
  survey: SurveyOut | null;
  selftest: SelftestSummary | null;
  program_author?: string | null;
  response_id?: string | null;
  regen_count?: number | null;
  models: string[];
  clip: { id?: string; source?: string; note?: string } | null;
  booklet: { id?: string; condition?: string; printed_disp_t?: number; page?: number } | null;
  facts?: Record<string, unknown>;
  footer: string;
  created_at: string;
}

export interface Attempt {
  attempt: number;
  response_id?: string;
  status?: string;
  minutes?: number;
  usage?: { input_tokens?: number; output_tokens?: number; total_tokens?: number };
  est_usd?: number;
  sha?: string;
  verdict: string;
  pass_count: number;
  n: number;
  probes?: boolean[];
  diff_max?: number | null;
  diff_fail?: number;
  error?: string | null;
  failing?: [string, string][];
  sandbox_ms?: number;
}

export interface ProgramMeta {
  booklet?: string;
  sha256: string;
  program_author: string;
  response_id?: string | null;
  regen_count?: number | null;
  note?: string;
}

export interface Program {
  meta: ProgramMeta;
  attempts: { manifest?: { pages?: number[]; leak_check?: string }; attempts: Attempt[] };
  code: string;
}

export interface ClipInfo {
  id: string;
  source?: string;
  fps?: number;
  frames?: number;
  scale?: number;
  box_wh?: [number, number];
  file?: string;
}

/** A full recorded run file; live runs stored in localStorage use the same shape (kind "live"). */
export interface Run {
  run_id: string;
  kind: RunKind;
  title: string;
  date: string;
  clip?: ClipInfo;
  geometry?: Geometry;
  labels?: Labels;
  draft?: { ok?: boolean; result: DraftResult; frames: DraftFrame[]; row1?: string | null };
  certificate: Certificate;
  selftest?: Selftest;
  program?: Program;
  usage?: UsageRow[];
  timing_ms?: Record<string, number>;
}
