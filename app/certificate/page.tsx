import { Suspense } from "react";
import { SiteHeader } from "@/components/SiteChrome";
import { LocalCertificate } from "./LocalCertificate";

export const metadata = { title: "Live certificate — DraftMark" };

/** /certificate?run=local — a live run's certificate, rendered in the browser from localStorage (no server storage). */
export default function LocalCertificatePage() {
  return (
    <>
      <div className="no-print">
        <SiteHeader />
      </div>
      <main className="page page--cert">
        <Suspense fallback={<p>Loading the certificate…</p>}>
          <LocalCertificate />
        </Suspense>
      </main>
    </>
  );
}
