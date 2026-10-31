import { SiteHeader } from "@/components/SiteChrome";
import { SurveyFlow } from "./SurveyFlow";

export const metadata = { title: "Live survey — DraftMark" };

export default function SurveyPage() {
  return (
    <>
      <SiteHeader live />
      <main className="page">
        <div className="section-head">
          <p className="eyebrow">Live · real API calls · each step opens when the previous one finishes</p>
          <h1 className="h1">Run a survey live</h1>
          <p className="muted">
            Six stations, top to bottom: clip, measure, labels, draft, program, survey. Every number below is printed by
            the API&apos;s code from this session&apos;s calls; nothing is stored on the server.
          </p>
        </div>
        <SurveyFlow />
      </main>
    </>
  );
}
