import {
  RecommendationsEmptyState,
  RecommendationsHeader,
  RecommendationsList,
  RecommendationsSearch,
} from "..";

import { useRecommendations } from "../hooks/useRecommendations";

import { useState } from "react";


export function RecommendationsView() {
  const {
    loading,
    error,
    recommendations,
  } = useRecommendations();

  const [query, setQuery] =
    useState("");


  if (loading) {
    return (
      <div>
        Loading recommendations...
      </div>
    );
  }


  if (error) {
    return (
      <div>
        Failed to load recommendations
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
      <RecommendationsHeader />

      <RecommendationsSearch
        value={query}
        onChange={setQuery}
        onSearch={() => {}}
      />

      {recommendations.length === 0 ? (
        <RecommendationsEmptyState />
      ) : (
        <RecommendationsList
          recommendations={recommendations}
        />
      )}
    </section>
  );
}