import type { ReactNode } from "react";

export type BadgeTone = "recorded" | "live" | "synthetic" | "caveat" | "degraded" | "proof";

export function Badge({ tone, children }: { tone: BadgeTone; children: ReactNode }) {
  return <span className={`badge badge--${tone}`}>{children}</span>;
}

export function Badges({ children }: { children: ReactNode }) {
  return <div className="badges">{children}</div>;
}
