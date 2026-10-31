export default function Home() {
  return (
    <main>
      <p className="muted data">DRAFTMARK · BUILD IN PROGRESS</p>
      <h1>Weigh a ship&apos;s cargo from a phone video of its draft marks.</h1>
      <p>
        SAM 3.1 tracks the painted draft numerals and the water surface frame by frame; code turns them into a
        wave-averaged draft with a stated uncertainty. Muse Wonder 1.0 reads the ship&apos;s stability booklet,
        writes a survey program for that ship, and must reproduce the booklet&apos;s own printed loading
        conditions before it may compute anything.
      </p>
      <p className="muted">
        Prototype — not a surveyor&apos;s certificate. Health: <a href="/api/py/health">/api/py/health</a>
      </p>
    </main>
  );
}
