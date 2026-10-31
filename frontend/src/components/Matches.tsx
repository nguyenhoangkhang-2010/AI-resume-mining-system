import type { JobMatch, RankedCandidate, ScoreBreakdown } from "../api/types";
import { Chips, ScoreBar, ScoreRing } from "./ui";

function Breakdown({ breakdown }: { breakdown: ScoreBreakdown | null | undefined }) {
  if (!breakdown) return null;

  const explanation = Object.values(breakdown.explanation ?? {});

  return (
    <details className="why">
      <summary>Why this score</summary>
      <ScoreBar label="Skills" value={breakdown.skill_score} />
      <ScoreBar label="Meaning" value={breakdown.semantic_score} />
      <ScoreBar label="Experience" value={breakdown.experience_score} />
      {breakdown.rerank_score != null && <ScoreBar label="Reranker" value={breakdown.rerank_score} />}
      {explanation.length > 0 && (
        <ul className="explain">
          {explanation.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      )}
    </details>
  );
}

function Rank({ rank }: { rank: number }) {
  return (
    <span className="rank" aria-label={`Rank ${rank}`}>
      {String(rank).padStart(2, "0")}
    </span>
  );
}

/** A candidate ranked for a job. */
export function CandidateMatch({ rank, match }: { rank: number; match: RankedCandidate }) {
  const profile = match.candidate_profile;
  const name = profile.personal_info?.full_name || "Unnamed candidate";
  const matched = match.score_breakdown?.matched_skills ?? [];
  const latest = profile.experience?.[0];

  return (
    <li className="card match">
      <Rank rank={rank} />

      <div className="match-body">
        <h3>{name}</h3>

        {latest && <p className="muted">{[latest.role, latest.company].filter(Boolean).join(" at ")}</p>}

        <Chips items={profile.skills ?? []} highlight={matched} />

        {(match.skill_gaps ?? []).length > 0 && (
          <p className="gaps">
            <strong>Missing</strong> {(match.skill_gaps ?? []).join(", ")}
          </p>
        )}

        <Breakdown breakdown={match.score_breakdown} />
      </div>

      <ScoreRing value={match.similarity_score} label="Match score" />
    </li>
  );
}

/** A job that fits a candidate. */
export function JobFit({ rank, match }: { rank: number; match: JobMatch }) {
  const facts = [match.location, match.experience_years ? `${match.experience_years}+ years` : null].filter(Boolean);

  return (
    <li className="card match">
      <Rank rank={rank} />

      <div className="match-body">
        <h3>{match.title}</h3>

        {facts.length > 0 && <p className="muted">{facts.join(" · ")}</p>}

        <Chips items={match.required_skills ?? []} highlight={match.score_breakdown.matched_skills ?? []} />

        {(match.skill_gaps ?? []).length > 0 && (
          <p className="gaps">
            <strong>Skills to add</strong> {(match.skill_gaps ?? []).join(", ")}
          </p>
        )}

        <Breakdown breakdown={match.score_breakdown} />
      </div>

      <ScoreRing value={match.score} label="Match score" />
    </li>
  );
}
