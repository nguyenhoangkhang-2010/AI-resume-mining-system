import {
  MatchingEmptyState,
  MatchingHeader,
  MatchingResultList,
  MatchingSearch,
} from "..";

import { useMatching } from "../hooks/useMatching";

import { useState } from "react";


export function MatchingView() {
  const {
    loading,
    error,
    matches,
  } = useMatching();

  const [query, setQuery] =
    useState("");


  if (loading) {
    return (
      <div>
        Loading matching results...
      </div>
    );
  }


  if (error) {
    return (
      <div>
        Failed to load matching results
      </div>
    );
  }


  return (
    <section
      className="
        flex
        flex-col
        gap-6
      "
    >
      <MatchingHeader />

      <MatchingSearch
        value={query}
        onChange={setQuery}
        onSearch={() => {}}
      />

      {matches.length === 0 ? (
        <MatchingEmptyState />
      ) : (
        <MatchingResultList
          matches={matches}
        />
      )}
    </section>
  );
}