/** Client-side upload limits; they mirror the server's checks in api/index.py (MAX_UPLOAD, fps, frames). */
export const MAX_BYTES = 3 * 1024 * 1024;
export const MAX_SECONDS = 10.5;
export const MAX_FPS = 8;
export const MAX_FRAMES = 64;
/** Mark systems the measurement code supports: metric ship marks (scale 1.0) and the 1:10 barge strip (0.1). */
export const MARK_SYSTEMS = {
  ship: { scale: 1.0, label: "Metric ship draft marks" },
  barge: { scale: 0.1, label: "1:10 barge strip" },
} as const;
export type MarkSystemId = keyof typeof MARK_SYSTEMS;
/** Dock density range for the ship sheet (t/m³) and the barge what-if control. */
export const SHIP_SG = { min: 1.0, max: 1.025, step: 0.001, init: 1.025 };
export const BARGE_WHAT_IF_SG = { min: 0.99, max: 1.005, step: 0.0005 };
