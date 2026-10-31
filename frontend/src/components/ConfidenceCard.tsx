import type { Confidence } from "../api/types";
import { COMPONENT_LABEL, confidencePercent, confidenceReason } from "../lib/format";
import { Badge, ScoreBar, ScoreRing } from "./ui";

const TONE = { high: "good", medium: "warn", low: "bad" } as const;

const MEANING = {
  high: "Every extraction measured at this level was right.",
  medium: "Read it: the extraction may have missed or mixed up entries.",
  low: "Probably wrong or incomplete. Read the CV yourself.",
} as const;

/** How far the extraction can be trusted, and why not fully. */
export function ConfidenceCard({ confidence }: { confidence: Confidence }) {
  const level = confidence.level;
  const components = Object.entries(confidence.components ?? {});

  return (
    <section className="card" aria-label="Extraction confidence">
      <header className="confidence-head">
        <ScoreRing
          value={confidencePercent(confidence.score)}
          label="Confidence"
          tone={TONE[level]}
          size="lg"
        />
        <div>
          <p className="eyebrow">How far to trust it</p>
          <h3>
            Extraction confidence{" "}
            <Badge tone={TONE[level]}>
              {confidencePercent(confidence.score)}% · {level}
            </Badge>
          </h3>
          <p className="muted">{MEANING[level]}</p>
        </div>
      </header>

      <div className="confidence-bars">
        {components.map(([name, value]) => (
          <ScoreBar key={name} label={COMPONENT_LABEL[name] ?? name} value={value * 100} />
        ))}
      </div>

      {(confidence.reasons ?? []).length > 0 && (
        <>
          <h4>What lowered it</h4>
          <ul className="reasons">
            {(confidence.reasons ?? []).map((reason) => (
              <li key={reason}>{confidenceReason(reason)}</li>
            ))}
          </ul>
        </>
      )}

      <p className="fineprint">
        A guide, not a probability. It catches empty or visibly broken extractions; it cannot catch a plausible
        but wrong entry.
      </p>
    </section>
  );
}
