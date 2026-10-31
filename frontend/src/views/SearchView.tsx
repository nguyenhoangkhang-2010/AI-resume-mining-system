import { useState } from "react";

import { useConnection } from "../app/context";
import type { SearchResponse } from "../api/types";
import { PRESET_QUERIES } from "../api/demo";
import { Chips, Empty, ErrorNotice, Icon, PageHead, ScoreRing } from "../components/ui";

/** Free-text search over the candidates, by meaning rather than by keyword. */
export function SearchView() {
  const { api } = useConnection();
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function run(text: string) {
    setBusy(true);
    setError(null);

    try {
      setResponse(await api.searchCandidates(text));
    } catch (failure) {
      setResponse(null);
      setError(failure);
    } finally {
      setBusy(false);
    }
  }

  const results = response?.results ?? [];

  return (
    <>
      <PageHead eyebrow="Step 3" title="Search candidates">
        Describe who you are looking for in a sentence. The search goes by meaning, not by exact keywords.
      </PageHead>

      <div className="stack narrow">
        <form
          className="searchbox"
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
            if (query.trim()) void run(query.trim());
          }}
        >
          <Icon name="search" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="backend engineer who knows Kubernetes and Postgres"
            aria-label="Query"
          />
          <button type="submit" className="btn" disabled={busy || !query.trim()}>
            {busy ? "Searching…" : "Search"}
          </button>
        </form>

        {api.mode === "demo" && (
          <div>
            <p className="fineprint">The recorded demo answers these questions only:</p>
            <ul className="chips">
              {PRESET_QUERIES.map((preset) => (
                <li key={preset}>
                  <button
                    type="button"
                    className="chip chip-button"
                    onClick={() => {
                      setQuery(preset);
                      void run(preset);
                    }}
                  >
                    {preset}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        <ErrorNotice error={error} />
        {response && results.length === 0 && <Empty>Nothing close enough.</Empty>}

        <ol className="matches">
          {results.map((hit) => (
            <li key={hit.candidate.id} className="card match">
              <div className="match-body">
                <h3>{hit.candidate.full_name || "Unnamed candidate"}</h3>
                <Chips items={(hit.candidate.skills ?? []).slice(0, 12)} />
              </div>
              <ScoreRing value={hit.score} label="Match score" />
            </li>
          ))}
        </ol>
      </div>
    </>
  );
}
