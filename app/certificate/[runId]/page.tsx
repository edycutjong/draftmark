import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { loadRun, runIndex } from "@/lib/runs";
import type { Run } from "@/lib/types";
import { Certificate } from "@/components/Certificate";
import { PrintButton } from "@/components/PrintButton";
import { SiteHeader } from "@/components/SiteChrome";

export const dynamicParams = false;

export function generateStaticParams() {
  return runIndex().map((r) => ({ runId: r.run_id }));
}

type Props = { params: Promise<{ runId: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { runId } = await params;
  return { title: `Certificate ${runId} — DraftMark` };
}

/** The certificate needs the per-frame drafts (small wave chart), not the per-frame geometry. */
function forCertificate(run: Run): Run {
  return run.geometry ? { ...run, geometry: { ...run.geometry, frames: [] } } : run;
}

export default async function CertificatePage({ params }: Props) {
  const { runId } = await params;
  const run = loadRun(runId);
  if (!run) notFound();
  return (
    <>
      <div className="no-print">
        <SiteHeader />
      </div>
      <main className="page page--cert">
        <div className="cert__actions no-print">
          <PrintButton />
        </div>
        <Certificate run={forCertificate(run)} />
      </main>
    </>
  );
}
