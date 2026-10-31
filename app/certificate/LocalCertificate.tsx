"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { Run } from "@/lib/types";
import { LOCAL_RUN_KEY } from "@/lib/api";
import { Certificate } from "@/components/Certificate";
import { PrintButton } from "@/components/PrintButton";

export function LocalCertificate() {
  const params = useSearchParams();
  const which = params.get("run");
  const [run, setRun] = useState<Run | null | undefined>(undefined);

  useEffect(() => {
    if (which !== "local") {
      setRun(null);
      return;
    }
    try {
      const raw = window.localStorage.getItem(LOCAL_RUN_KEY);
      setRun(raw ? (JSON.parse(raw) as Run) : null);
    } catch {
      setRun(null);
    }
  }, [which]);

  if (run === undefined) return <p>Loading the certificate…</p>;
  if (run === null || !run.certificate)
    return (
      <div className="empty">
        <h1 className="h2">No live run in this browser</h1>
        <p>
          Live certificates are kept only in this browser. Finish a run on the <Link href="/survey">live survey</Link>, or
          open a <Link href="/runs">recorded run</Link>.
        </p>
      </div>
    );
  return (
    <>
      <div className="cert__actions no-print">
        <PrintButton />
      </div>
      <Certificate run={run} />
    </>
  );
}
