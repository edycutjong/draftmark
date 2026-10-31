"use client";

import { Children, useState, type ReactNode } from "react";

/** Accessible tabs over server-rendered panels (panels stay mounted; inactive ones are hidden). */
export function Tabs({ tabs, label, children }: { tabs: { id: string; label: ReactNode }[]; label: string; children: ReactNode }) {
  const [active, setActive] = useState(0);
  const panels = Children.toArray(children);
  function onKey(e: React.KeyboardEvent<HTMLButtonElement>, k: number) {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const next = (k + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length;
    setActive(next);
    document.getElementById(`tab-${tabs[next].id}`)?.focus();
  }
  return (
    <div className="tabset">
      <div className="tabs" role="tablist" aria-label={label}>
        {tabs.map((t, k) => (
          <button
            key={t.id}
            id={`tab-${t.id}`}
            type="button"
            role="tab"
            className="tab"
            aria-selected={active === k}
            aria-controls={`panel-${t.id}`}
            tabIndex={active === k ? 0 : -1}
            onClick={() => setActive(k)}
            onKeyDown={(e) => onKey(e, k)}
          >
            {t.label}
          </button>
        ))}
      </div>
      {panels.map((p, k) => (
        <div key={tabs[k]?.id ?? k} id={`panel-${tabs[k]?.id}`} role="tabpanel" aria-labelledby={`tab-${tabs[k]?.id}`} hidden={active !== k}>
          {p}
        </div>
      ))}
    </div>
  );
}
