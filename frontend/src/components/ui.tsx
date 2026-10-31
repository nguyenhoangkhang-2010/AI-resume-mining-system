import type { ReactNode } from "react";

import { ApiError } from "../api/types";

export function Chips({ items, highlight = [] }: { items: string[]; highlight?: string[] }) {
  if (items.length === 0) return null;

  const marked = new Set(highlight.map((item) => item.toLowerCase()));

  return (
    <ul className="chips">
      {items.map((item) => (
        <li key={item} className={marked.has(item.toLowerCase()) ? "chip chip-match" : "chip"}>
          {item}
        </li>
      ))}
    </ul>
  );
}

/** A labelled bar for a value between 0 and `max`. */
export function ScoreBar({
  label,
  value,
  max = 100,
  suffix = "%",
}: {
  label: string;
  value: number | null | undefined;
  max?: number;
  suffix?: string;
}) {
  const known = value !== null && value !== undefined;
  const width = known ? Math.max(0, Math.min(100, (value / max) * 100)) : 0;

  return (
    <div className="bar">
      <span className="bar-label">{label}</span>
      <span className="bar-track" role="img" aria-label={`${label}: ${known ? Math.round(value) : "n/a"}`}>
        <span className="bar-fill" style={{ width: `${width}%` }} />
      </span>
      <span className="bar-value">{known ? `${Math.round(value)}${suffix}` : "–"}</span>
    </div>
  );
}

const RING_RADIUS = 21;
const RING_LENGTH = 2 * Math.PI * RING_RADIUS;

/** A number inside a ring that fills in proportion to it (0 to 100). */
export function ScoreRing({
  value,
  label,
  tone = "accent",
  size = "md",
}: {
  value: number;
  label: string;
  tone?: "accent" | "good" | "warn" | "bad";
  size?: "md" | "lg";
}) {
  const shown = Math.max(0, Math.min(100, Math.round(value)));

  return (
    <span className={`ring ring-${tone} ring-${size}`} role="img" aria-label={`${label}: ${shown}`}>
      <svg viewBox="0 0 50 50" aria-hidden="true">
        <circle className="ring-track" cx="25" cy="25" r={RING_RADIUS} />
        <circle
          className="ring-fill"
          cx="25"
          cy="25"
          r={RING_RADIUS}
          strokeDasharray={RING_LENGTH}
          strokeDashoffset={RING_LENGTH * (1 - shown / 100)}
        />
      </svg>
      <span className="ring-value" aria-hidden="true">
        {shown}
      </span>
    </span>
  );
}

export function Badge({ tone, children }: { tone: "good" | "warn" | "bad" | "neutral"; children: ReactNode }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

/** Title block at the top of every screen. */
export function PageHead({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) {
  return (
    <header className="page-head">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      {children && <p className="lead">{children}</p>}
    </header>
  );
}

/** The steps a CV goes through; `at` is the step in progress (steps.length = all done). */
export function Steps({ steps, at, failed }: { steps: string[]; at: number; failed?: boolean }) {
  return (
    <ol className="steps" aria-label="Progress">
      {steps.map((step, index) => {
        const state = index < at ? "done" : index === at ? "now" : "next";
        const bad = failed && index === steps.length - 1 && index <= at;

        return (
          <li key={step} className={`step step-${bad ? "bad" : state}`} aria-current={state === "now" ? "step" : undefined}>
            <span className="step-dot" aria-hidden="true" />
            <span className="step-name">{step}</span>
          </li>
        );
      })}
    </ol>
  );
}

const ICONS = {
  upload: "M12 16V4m0 0L7 9m5-5 5 5M4 16v2.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V16",
  briefcase: "M4 8h16v11H4zM9 8V6a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M4 13h16",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zm9 2-4.2-4.2",
  files: "M7 3h7l4 4v13H7zM14 3v4h4M10 12h5M10 16h5",
  check: "m5 12.5 4.5 4.5L19 7.5",
  plug: "M9 3v5m6-5v5M6 8h12v3a6 6 0 0 1-12 0zm6 9v4",
} as const;

export function Icon({ name }: { name: keyof typeof ICONS }) {
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d={ICONS[name]} />
    </svg>
  );
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return "The API key is missing or wrong. Enter it in the connection panel.";
    if (error.status === 403) return "This key is not allowed to do that (an admin key is needed).";
    if (error.status === 429) {
      return `Too many requests${error.retryAfter ? `: try again in ${error.retryAfter} s` : ""}.`;
    }

    return error.message;
  }

  return error instanceof Error ? error.message : "Something went wrong.";
}

export function ErrorNotice({ error }: { error: unknown }) {
  if (!error) return null;

  return (
    <p className="notice notice-bad" role="alert">
      {errorMessage(error)}
    </p>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>;
}
