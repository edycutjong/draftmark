import Link from "next/link";

/** Brand mark: the landing's icon (the 8 numeral on the hull band), so / and the app share one mark. */
export function BrandMark() {
  // eslint-disable-next-line @next/next/no-img-element
  return <img className="brandmark" src="/icon.svg" alt="" width={30} height={30} />;
}

export function SiteHeader({ live }: { live?: boolean }) {
  return (
    <header className="site-header">
      <a href="/" className="brand" aria-label="DraftMark home">
        <BrandMark />
        <span className="brand__word">DRAFTMARK</span>
      </a>
      <nav aria-label="Main">
        <ul className="nav">
          <li>
            <Link href="/runs">Recorded runs</Link>
          </li>
          <li>
            <Link href="/evidence">Evidence</Link>
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
