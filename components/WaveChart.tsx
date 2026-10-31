import type { DraftFrame, DraftResult } from "@/lib/types";
import { fx, isNum } from "@/lib/format";

/** The signature element: the per-frame draft trace jumps with the swell; the running mean of the kept
 *  frames settles onto the clip result d, inside a band that narrows as frames accumulate.
 *  Band at the k-th kept frame = final repeatability u x sqrt(N_kept / k), so it closes exactly on u. */
export function WaveChart({
  id,
  frames,
  result,
  markScale = 1,
  animate = true,
  small = false,
}: {
  id: string;
  frames: DraftFrame[];
  result: DraftResult;
  markScale?: number;
  animate?: boolean;
  small?: boolean;
}) {
  const W = 680;
  const H = small ? 220 : 320;
  const m = { l: 58, r: 132, t: 18, b: 40 };
  const pw = W - m.l - m.r;
  const ph = H - m.t - m.b;
  const n = Math.max(frames.length, result.n_frames ?? 0, 2);
  const kept = frames.filter((f) => f.kept && isNum(f.d_m));
  const dropped = frames.filter((f) => !f.kept);
  const d = result.d_m;
  const u = result.u_rep_m ?? 0;

  const vals = kept.map((f) => f.d_m as number);
  if (isNum(d)) vals.push(d + u, d - u);
  if (result.swell_p5_p95) vals.push(...result.swell_p5_p95);
  const lo0 = vals.length ? Math.min(...vals) : 0;
  const hi0 = vals.length ? Math.max(...vals) : 1;
  const span = hi0 - lo0 || 0.1 * markScale;
  const lo = lo0 - span * 0.18;
  const hi = hi0 + span * 0.18;

  const x = (i: number) => m.l + (i / (n - 1)) * pw;
  const y = (v: number) => m.t + (1 - (v - lo) / (hi - lo)) * ph;

  // running mean + narrowing band over the kept frames, in frame order
  const run: { i: number; mean: number; band: number }[] = [];
  let sum = 0;
  kept.forEach((f, k) => {
    sum += f.d_m as number;
    run.push({ i: f.i, mean: sum / (k + 1), band: u * Math.sqrt(kept.length / (k + 1)) });
  });

  // y ticks on the painted-mark pitch of this mark system
  let step = 0.2 * markScale;
  const count = () => Math.floor(hi / step) - Math.ceil(lo / step) + 1;
  while (count() < 3 && step > 1e-6) step /= 2;
  while (count() > 7) step *= 2;
  const ticks: number[] = [];
  for (let k = Math.ceil(lo / step); k <= Math.floor(hi / step); k++) ticks.push(k * step);
  const tickDigits = markScale < 1 ? 3 : step < 0.1 ? 2 : 1;

  const tracePts = kept.map((f) => `${x(f.i)},${y(f.d_m as number)}`).join(" ");
  const meanPts = run.map((r) => `${x(r.i)},${y(r.mean)}`).join(" ");
  const bandPts = [
    ...run.map((r) => `${x(r.i)},${y(r.mean + r.band)}`),
    ...run
      .slice()
      .reverse()
      .map((r) => `${x(r.i)},${y(r.mean - r.band)}`),
  ].join(" ");
  const last = run[run.length - 1];
  const clip = `wave-clip-${id}`;
  const reveal = `wave-reveal-${id}`;

  return (
    <figure className={`wave${animate ? " wave--animate" : ""}`}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby={`${clip}-t`} className="wave__svg">
        <title id={`${clip}-t`}>
          {`Per-frame draft over ${n} frames with the running mean settling to ${fx(d)} m ± ${fx(u)} m`}
        </title>
        <defs>
          <clipPath id={clip}>
            <rect x={m.l} y={m.t} width={pw + 2} height={ph} />
          </clipPath>
          <clipPath id={reveal}>
            <rect className="wave__reveal" x={m.l - 4} y={0} width={pw + m.r + 4} height={H} />
          </clipPath>
        </defs>
        {ticks.map((t) => (
          <g key={t} className="wave__tick">
            <line x1={m.l} x2={m.l + pw} y1={y(t)} y2={y(t)} />
            <text x={m.l - 8} y={y(t) + 4} textAnchor="end">
              {t.toFixed(tickDigits)}
            </text>
          </g>
        ))}
        <text className="wave__axis" x={m.l} y={H - 8}>
          frame 0
        </text>
        <text className="wave__axis" x={m.l + pw} y={H - 8} textAnchor="end">
          {`frame ${n - 1}`}
        </text>
        <g clipPath={`url(#${clip})`}>
          {result.swell_p5_p95 ? (
            <rect
              className="wave__swell"
              x={m.l}
              width={pw}
              y={y(result.swell_p5_p95[1])}
              height={Math.max(0, y(result.swell_p5_p95[0]) - y(result.swell_p5_p95[1]))}
            />
          ) : null}
          <polyline className="wave__trace" points={tracePts} />
          {kept.map((f) => (
            <circle key={f.i} className="wave__dot" cx={x(f.i)} cy={y(f.d_m as number)} r={small ? 2 : 2.6} />
          ))}
          <g clipPath={`url(#${reveal})`}>
            <polygon className="wave__band" points={bandPts} />
            <polyline className="wave__mean" points={meanPts} />
          </g>
        </g>
        {dropped.map((f) => (
          <g key={`x${f.i}`} className="wave__drop">
            <title>{`frame ${f.i} dropped: ${f.drop_reason}`}</title>
            <line x1={x(f.i)} x2={x(f.i)} y1={m.t + ph - 10} y2={m.t + ph} />
          </g>
        ))}
        {last && isNum(d) ? (
          <g className="wave__final">
            <line x1={x(last.i)} x2={m.l + pw + 10} y1={y(d)} y2={y(d)} />
            <text className="wave__value" x={m.l + pw + 14} y={y(d) + 6}>
              {fx(d)}
            </text>
            <text className="wave__pm" x={m.l + pw + 14} y={y(d) + 24}>
              {`± ${fx(u)} m`}
            </text>
          </g>
        ) : null}
      </svg>
      <figcaption className="wave__legend">
        <span className="key key--before">per-frame draft</span>
        <span className="key key--after">running mean (band: illustrative, narrows to ± u)</span>
        <span className="key key--swell">swell p5–p95</span>
        {dropped.length ? <span className="key key--drop">dropped frame</span> : null}
      </figcaption>
    </figure>
  );
}
