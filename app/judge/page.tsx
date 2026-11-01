import Link from "next/link";
import { loadRun } from "@/lib/runs";
import { SiteHeader } from "@/components/SiteChrome";

export const dynamic = "force-static";
export const metadata = { title: "Judge path — DraftMark" };

const CLIP = "rec-db7x-20261031";
const BOOKLET = "rec-trieste-20261031";

/** /judge — the two-minute path through the product for a judge: no upload, no code. Numbers come from the run files. */
export default function JudgePage() {
  const clip = loadRun(CLIP);
  const booklet = loadRun(BOOKLET);
  const d = clip?.draft?.result;
  const st = booklet?.certificate?.selftest;
  const disp = booklet?.certificate?.survey?.disp;
  return (
    <>
      <SiteHeader />
      <main className="page">
        <p className="eyebrow">For judges · about two minutes · no upload, no code</p>
        <h1 className="h1">Judge path</h1>
        <p className="lede">
          Four stops, in order. Step 1 runs live on this deployment; steps 2 to 4 open recorded runs whose Meta API
          calls are listed, with response ids, on <Link href="/evidence">/evidence</Link>.
        </p>

        <ol className="judge-steps">
          <li>
            <h2 className="h3">Re-run the program Muse Wonder 1.0 wrote, live</h2>
            <p>
              The sandbox re-runs the saved program against the booklet&apos;s printed conditions (
              <span className="data">{st ? `${st.pass_count}/${st.n}` : "22/22"}</span> at record time). This is the only step
              that executes now.
            </p>
            <p>
              <Link href="/runs#program-h" className="btn btn--accent">Open the self-test →</Link>
            </p>
          </li>
          <li>
            <h2 className="h3">Watch one real hull get measured, then refused</h2>
            <p>
              Clip dB7X (third-party test footage, no ground truth): SAM 3.1 tracks the numerals and the water in every
              frame, Muse Spark 1.3 reads the labels and five code checks confirm them, code averages the swell to{" "}
              <span className="data">
                {d?.d_m != null ? d.d_m.toFixed(3) : "12.761"} m ± {d?.u_rep_m != null ? d.u_rep_m.toFixed(3) : "0.086"} m
              </span>{" "}
              (repeatability). The draft is past the only booklet&apos;s table, so the certificate refuses:{" "}
              <span className="data">{clip?.certificate?.decision ?? "REFUSE"} · {clip?.certificate?.reason ?? "OUT_OF_TABLE"}</span>.
            </p>
            <p>
              <Link href="/runs#measurement-h">Open the recorded measurement →</Link>
            </p>
          </li>
          <li>
            <h2 className="h3">See Wonder&apos;s three attempts</h2>
            <p>
              Attempt 1 was rejected by the sandbox&apos;s code gate, attempt 2 reproduced 14 of 22 conditions, attempt 3
              reproduced 22 of 22. Only the failing condition ids and Wonder&apos;s own intermediate values were fed back; the
              printed answers were never in its prompt.
            </p>
            <p>
              <Link href="/runs#program-h">Open the program and its attempts →</Link>
            </p>
          </li>
          <li>
            <h2 className="h3">Open the two certificates</h2>
            <p>
              The refusal for the real hull, and the issued survey on the booklet&apos;s own ship (condition 4.1, all six drafts
              entered):{" "}
              <span className="data">{disp != null ? disp.toFixed(1) : "17825.8"} t</span> against the printed 17827.7 t, issued
              with a warning; cargo not computed.
            </p>
            <p>
              <Link href={`/certificate/${CLIP}`}>Refusal certificate →</Link>{" "}
              <Link href={`/certificate/${BOOKLET}`}>Issued certificate →</Link>
            </p>
          </li>
        </ol>

        <h2 className="h2">Optional: run SAM 3.1 and Spark 1.3 live</h2>
        <p>
          <Link href="/survey">/survey</Link> measures your own prepared draft-mark clip (MP4, cropped to the mark column,
          at most 10.5 s, 64 frames and 3 MB). Uploads need the judge code from the submission notes. Our real-hull test
          clips are third-party footage we may not re-host.
        </p>

        <aside className="honesty" aria-label="What this does not prove">
          <h2 className="h4">What this does not prove</h2>
          <ul>
            <li>Weight accuracy is shown only on a barge rendered by code; there is no physical scale check yet.</li>
            <li>The real-hull clips have no ground truth: repeatability and refusal only.</li>
            <li>The only booklet is a Ro-Ro/passenger ship, not a bulk carrier. Prototype, not a surveyor&apos;s certificate.</li>
          </ul>
        </aside>

        <p className="small muted">
          Also: <a href="https://youtu.be/9vRaziU6X1g">demo video</a> · <Link href="/deck">pitch deck</Link> ·{" "}
          <a href="https://github.com/edycutjong/draftmark">source (MIT)</a>
        </p>
      </main>
    </>
  );
}
