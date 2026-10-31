import type { DraftFrame, GeomFrame } from "@/lib/types";
import { fx, isNum } from "@/lib/format";

/** SVG schematic of one frame from the compact geometry: SAM token boxes, the water surface profile,
 *  the fitted draft scale (y = a + b * draft) and the water-edge line. No video pixels.
 *  With `size` the viewBox is the intrinsic video frame, so it can sit exactly on top of a <video>. */
export function Overlay({
  frame,
  column,
  fit,
  labels,
  drafts,
  size,
  title,
}: {
  frame: GeomFrame;
  column: [number, number] | null;
  fit?: DraftFrame | null;
  labels?: Record<string, string>;
  drafts?: Record<string, number>;
  size?: { w: number; h: number };
  title?: string;
}) {
  const x0c = column?.[0] ?? 0;
  const water = frame.water
    .map((y, k) => (isNum(y) ? ([x0c + k, y] as [number, number]) : null))
    .filter((p): p is [number, number] => p !== null);
  const tx0 = Math.min(...frame.tokens.map((t) => t.box[0]), column?.[0] ?? Infinity);
  const tx1 = Math.max(...frame.tokens.map((t) => t.box[2]), column?.[1] ?? -Infinity);
  const ty0 = Math.min(...frame.tokens.map((t) => t.box[1]), ...water.map((p) => p[1]));
  const ty1 = Math.max(...frame.tokens.map((t) => t.box[3]), ...water.map((p) => p[1]));
  const vb = size
    ? { x: 0, y: 0, w: size.w, h: size.h }
    : (() => {
        const w0 = Number.isFinite(tx1 - tx0) ? tx1 - tx0 : 200;
        const pad = Math.max(24, w0 * 0.25);
        const x = tx0 - pad * 1.6;
        const y = (Number.isFinite(ty0) ? ty0 : 0) - pad;
        return { x, y, w: w0 + pad * 4.2, h: (Number.isFinite(ty1 - ty0) ? ty1 - ty0 : 400) + pad * 2.4 };
      })();
  const fs = size ? Math.max(9, Math.min(vb.w, vb.h) / 18) : Math.max(9, Math.min(vb.w / 9, vb.h / 14));
  const scaleX = (Number.isFinite(tx1) ? tx1 : vb.x + vb.w / 2) + fs * 0.9;
  const hasFit = fit && isNum(fit.a) && isNum(fit.b);
  const ticks =
    hasFit && drafts
      ? frame.tokens
          .filter((t) => isNum(drafts[t.track]))
          .map((t) => ({ z: drafts[t.track], y: (fit!.a as number) + (fit!.b as number) * drafts[t.track] }))
      : [];
  const yb = vb.y + vb.h;
  return (
    <svg
      className={`overlay${size ? " overlay--on-video" : ""}`}
      viewBox={`${vb.x} ${vb.y} ${vb.w} ${vb.h}`}
      preserveAspectRatio={size ? "none" : "xMidYMid meet"}
      role="img"
      aria-label={title ?? `Frame ${frame.i}: ${frame.tokens.length} mark tokens and the water surface`}
    >
      {!size ? <rect x={vb.x} y={vb.y} width={vb.w} height={vb.h} className="overlay__bg" /> : null}
      {water.length > 1 ? (
        <>
          <polygon
            className="overlay__sea"
            points={[...water.map((p) => p.join(",")), `${water[water.length - 1][0]},${yb}`, `${water[0][0]},${yb}`].join(" ")}
          />
          <polyline className="overlay__surface" points={water.map((p) => p.join(",")).join(" ")} />
        </>
      ) : null}
      {frame.tokens.map((t) => (
        <g key={t.track}>
          <rect
            className="overlay__token"
            x={t.box[0]}
            y={t.box[1]}
            width={t.box[2] - t.box[0]}
            height={t.box[3] - t.box[1]}
            strokeWidth={fs / 8}
          />
          {labels?.[t.track] ? (
            <text className="overlay__label" x={t.box[0] - fs * 0.35} y={t.box[3]} fontSize={fs} textAnchor="end">
              {labels[t.track]}
            </text>
          ) : (
            <text className="overlay__track" x={t.box[0] - fs * 0.35} y={t.box[3]} fontSize={fs * 0.7} textAnchor="end">
              {t.track}
            </text>
          )}
        </g>
      ))}
      {ticks.length ? (
        <g className="overlay__scale">
          <line
            x1={scaleX}
            x2={scaleX}
            y1={Math.min(...ticks.map((t) => t.y))}
            y2={isNum(fit?.water_edge_y) ? fit!.water_edge_y! : Math.max(...ticks.map((t) => t.y))}
            strokeWidth={fs / 10}
          />
          {ticks.map((t) => (
            <g key={t.z}>
              <line x1={scaleX} x2={scaleX + fs * 0.5} y1={t.y} y2={t.y} strokeWidth={fs / 10} />
              <text x={scaleX + fs * 0.7} y={t.y + fs * 0.3} fontSize={fs * 0.62}>
                {fx(t.z, Math.abs(t.z) < 1 ? 2 : 1)}
              </text>
            </g>
          ))}
        </g>
      ) : null}
      {hasFit && isNum(fit!.water_edge_y) ? (
        <g className="overlay__edge">
          <line x1={x0c - fs} x2={scaleX + fs * 0.5} y1={fit!.water_edge_y!} y2={fit!.water_edge_y!} strokeWidth={fs / 7} />
          {isNum(fit!.d_m) ? (
            <text x={scaleX + fs * 0.7} y={fit!.water_edge_y! + fs * 1.15} fontSize={fs * 0.72}>
              {fx(fit!.d_m)} m
            </text>
          ) : null}
        </g>
      ) : null}
      {fit && !fit.kept ? (
        <text className="overlay__drop" x={vb.x + fs * 0.5} y={vb.y + fs * 1.2} fontSize={fs * 0.7}>
          dropped: {fit.drop_reason}
        </text>
      ) : null}
    </svg>
  );
}
