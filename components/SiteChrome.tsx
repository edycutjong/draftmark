import Link from "next/link";

/** Brand mark: a short draft-scale column (ticks on the 20 cm pitch) crossed by the waterline. */
export function BrandMark() {
  const ticks = [0, 1, 2, 3, 4, 5];
  return (
    <svg className="brandmark" viewBox="0 0 28 40" aria-hidden="true">
      {ticks.map((k) => (
        <rect key={k} x={k % 5 === 0 ? 4 : 10} y={4 + k * 6} width={k % 5 === 0 ? 16 : 10} height="3" className="brandmark__tick" />
      ))}
      <rect x="0" y="27" width="28" height="2" className="brandmark__line" />
    </svg>
  );
}

export function SiteHeader({ live }: { live?: boolean }) {
  return (
    <header className="site-header">
      <Link href="/" className="brand" aria-label="DraftMark, recorded runs">
        <BrandMark />
        <span className="brand__word">DRAFTMARK</span>
      </Link>
      <nav aria-label="Main">
        <ul className="nav">
          <li>
            <Link href="/">Recorded runs</Link>
          </li>
          <li>
            {live ? (
              <span aria-current="page" className="nav__current">
                Live survey
              </span>
            ) : (
              <Link href="/survey" className="btn btn--accent">
                Run it live →
              </Link>
            )}
          </li>
        </ul>
      </nav>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <p>Prototype — not a surveyor&apos;s certificate.</p>
    </footer>
  );
}

/** The waterline rule between the two proofs: content above and below it is never merged. */
export function Waterline({ label }: { label: string }) {
  return (
    <div className="waterline" role="separator" aria-label={label}>
      <span>{label}</span>
    </div>
  );
}
