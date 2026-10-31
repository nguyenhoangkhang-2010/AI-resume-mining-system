import { useEffect, useState } from "react";

import { useConnection } from "../app/context";
import type { ResumePage } from "../api/types";
import { Badge, Empty, ErrorNotice, PageHead } from "../components/ui";
import { confidencePercent, statusLabel, statusReason, warningText } from "../lib/format";

const TONE = { processed: "good", needs_review: "warn", failed: "bad" } as const;
const FILTERS = ["all", "processed", "needs_review", "failed", "pending"] as const;

/** Every uploaded CV with its state: what needs a person to look at it. */
export function ResumesView() {
  const { api } = useConnection();
  const [page, setPage] = useState<ResumePage | null>(null);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api.listResumes().then(setPage).catch(setError);
  }, [api]);

  const all = page?.items ?? [];
  const items = all.filter((item) => filter === "all" || item.status === filter);
  const count = (name: (typeof FILTERS)[number]) =>
    name === "all" ? all.length : all.filter((item) => item.status === name).length;

  return (
    <>
      <PageHead eyebrow="Step 4" title="Resumes">
        Every CV that was uploaded and where it stands. Those held for review are the ones to read yourself.
      </PageHead>

      <div className="stack narrow">
        <div role="group" aria-label="Filter by state" className="filters">
          {FILTERS.map((name) => (
            <button
              key={name}
              type="button"
              aria-pressed={filter === name}
              className={filter === name ? "chip chip-button chip-on" : "chip chip-button"}
              onClick={() => setFilter(name)}
            >
              {name === "all" ? "All" : statusLabel(name)} <span className="count">{count(name)}</span>
            </button>
          ))}
        </div>

        <ErrorNotice error={error} />
        {page && items.length === 0 && <Empty>Nothing in this state.</Empty>}

        <ul className="list">
          {items.map((item) => (
            <li key={item.id} className="card resume">
              <header className="card-head">
                <h3>{item.filename}</h3>
                <Badge tone={item.status in TONE ? TONE[item.status as keyof typeof TONE] : "neutral"}>
                  {statusLabel(item.status)}
                </Badge>
              </header>
              <p className="muted">
                {new Date(item.created_at).toLocaleString()}
                {item.confidence && ` · confidence ${confidencePercent(item.confidence.score)}% (${item.confidence.level})`}
              </p>
              {item.reason && <p className="muted">{statusReason(item.reason)}</p>}
              {(item.warnings ?? []).length > 0 && (
                <ul className="reasons">
                  {item.warnings!.map((warning) => (
                    <li key={warning}>{warningText(warning)}</li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}
