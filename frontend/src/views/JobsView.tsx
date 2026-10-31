import { useCallback, useEffect, useState } from "react";

import { useConnection } from "../app/context";
import type { JobPage, Match } from "../api/types";
import { CandidateMatch } from "../components/Matches";
import { Chips, Empty, ErrorNotice, PageHead } from "../components/ui";

function facts(job: { location?: string | null; experience_years?: number | null }): string {
  return [job.location, job.experience_years ? `${job.experience_years}+ years` : null].filter(Boolean).join(" · ");
}

/** Create a job, pick one, and see the candidates ranked for it. */
export function JobsView() {
  const { api } = useConnection();
  const [jobs, setJobs] = useState<JobPage | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [match, setMatch] = useState<Match | null>(null);
  const [title, setTitle] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    api.listJobs().then(setJobs).catch(setError);
  }, [api]);

  useEffect(refresh, [refresh]);

  function choose(id: string) {
    setSelected(id);
    setMatch(null);
    setError(null);
    api.matchCandidates(id).then(setMatch).catch(setError);
  }

  async function create(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);

    try {
      const created = await api.createJob({
        title: title.trim(),
        description: description.trim(),
        location: location.trim() || undefined,
      });
      setTitle("");
      setLocation("");
      setDescription("");
      refresh();
      choose(created._id);
    } catch (failure) {
      setError(failure);
    } finally {
      setBusy(false);
    }
  }

  const results = match?.results ?? [];
  const current = (jobs?.items ?? []).find((job) => job.id === selected);

  return (
    <>
      <PageHead eyebrow="Step 2" title="Jobs and their candidates">
        Pick a job to rank the candidates for it. Each score comes with the reasons behind it.
      </PageHead>

      <div className="grid">
        <section className="stack">
          {api.mode === "live" && (
            <details className="card disclosure" open={(jobs?.items ?? []).length === 0}>
              <summary>New job</summary>
              <form onSubmit={create}>
                <label>
                  Title
                  <input value={title} onChange={(event) => setTitle(event.target.value)} required maxLength={200} />
                </label>
                <label>
                  Location (optional)
                  <input value={location} onChange={(event) => setLocation(event.target.value)} maxLength={120} />
                </label>
                <label>
                  Description
                  <textarea
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    rows={7}
                    required
                  />
                </label>
                <button type="submit" className="btn" disabled={busy || !title.trim() || !description.trim()}>
                  {busy ? "Reading the description…" : "Create job"}
                </button>
                <p className="fineprint">Skills, years and responsibilities are extracted from the text.</p>
              </form>
            </details>
          )}

          <div className="stack">
            <h2>Open jobs</h2>
            {jobs && jobs.items?.length === 0 && <Empty>No jobs yet.</Empty>}
            <ul className="list">
              {(jobs?.items ?? []).map((job) => (
                <li key={job.id}>
                  <button
                    type="button"
                    className={job.id === selected ? "row row-active" : "row"}
                    aria-pressed={job.id === selected}
                    onClick={() => choose(job.id)}
                  >
                    <strong>{job.title}</strong>
                    {facts(job) && <span className="muted">{facts(job)}</span>}
                    <Chips items={(job.required_skills ?? []).slice(0, 6)} />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="stack">
          <div className="result-head">
            <h2>{current ? current.title : "Candidates for this job"}</h2>
            {current && facts(current) && <p className="muted">{facts(current)}</p>}
          </div>
          <ErrorNotice error={error} />
          {!selected && <Empty>Pick a job to rank the candidates.</Empty>}
          {selected && !match && !error && <p className="muted">Ranking…</p>}
          {match && results.length === 0 && (
            <Empty>
              No candidate reaches the minimum score ({match.metadata.filtered_candidates} of{" "}
              {match.metadata.total_candidates} were filtered out).
            </Empty>
          )}
          <ol className="matches">
            {results.map((result, index) => (
              <CandidateMatch key={result.candidate_profile.resume_id} rank={index + 1} match={result} />
            ))}
          </ol>
          {match && results.length > 0 && (
            <p className="fineprint">
              {match.metadata.ranked_candidates} ranked, {match.metadata.filtered_candidates} below the minimum score.
              Scores order candidates for a person to read; they are not a judgement of ability.
            </p>
          )}
        </section>
      </div>
    </>
  );
}
