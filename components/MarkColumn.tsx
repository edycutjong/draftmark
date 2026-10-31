import { fx, isNum } from "@/lib/format";

/** Header motif: the painted mark column of a recorded clip, set by draft value (bottom to top, as painted),
 *  with the measured mean line crossing it. Marks and d come from the run JSON. */
export function MarkColumn({
  marks,
  d,
  u,
}: {
  marks: { label: string; draft: number }[];
  d: number | null;
  u: number | null;
}) {
  if (marks.length < 2) return null;
  const sorted = [...marks].sort((a, b) => a.draft - b.draft);
  const lo = sorted[0].draft;
  const hi = sorted[sorted.length - 1].draft;
  const pitch = (hi - lo) / (sorted.length - 1);
  const z0 = lo - pitch * 0.9;
  const z1 = hi + pitch * 0.7;
  const H = 360;
  const W = 220;
  const y = (z: number) => H - ((z - z0) / (z1 - z0)) * H;
  const digitH = Math.abs(y(lo + pitch / 2) - y(lo));
  return (
    <svg className="markcol" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Painted draft marks with the measured mean at ${fx(d)} m`}>
      <rect x="0" y="0" width={W} height={isNum(d) ? y(d) : H} className="markcol__hull" />
      {isNum(d) ? <rect x="0" y={y(d)} width={W} height={H - y(d)} className="markcol__sea" /> : null}
      {sorted.map((m) => (
        <text
          key={`${m.label}-${m.draft}`}
          x={m.label.endsWith("M") ? 18 : 44}
          y={y(m.draft)}
          className="markcol__mark"
          fontSize={digitH * 1.05}
        >
          {m.label}
        </text>
      ))}
      {isNum(d) ? (
        <g className="markcol__mean">
          {isNum(u) ? <rect x="0" y={y(d + u)} width={W} height={Math.max(1, y(d - u) - y(d + u))} className="markcol__band" /> : null}
          <line x1="0" x2={W} y1={y(d)} y2={y(d)} />
          <text x={W - 6} y={y(d) - 8} textAnchor="end" className="markcol__value">
            {fx(d)} m
          </text>
        </g>
      ) : null}
    </svg>
  );
}
