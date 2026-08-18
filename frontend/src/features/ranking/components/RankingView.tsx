import {
  RankingEmptyState,
  RankingHeader,
  RankingResultList,
  RankingSearch,
} from "..";

import { useRanking } from "../hooks/useRanking";

import { useState } from "react";


export function RankingView() {
  const {
    loading,
    error,
    rankings,
  } = useRanking();

  const [query, setQuery] =
    useState("");


  if (loading) {
    return (
      <div>
        Loading rankings...
      </div>
    );
  }


  if (error) {
    return (
      <div>
        Failed to load rankings
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
      <RankingHeader />

      <RankingSearch
        value={query}
        onChange={setQuery}
        onSearch={() => {}}
      />

      {rankings.length === 0 ? (
        <RankingEmptyState />
      ) : (
        <RankingResultList
          rankings={rankings}
        />
      )}
    </section>
  );
}