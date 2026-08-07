import { useMemo, useState } from "react";

import type { Recommendation } from "../types/recommendation";


interface UseRecommendationsResult {
  loading: boolean;
  error: Error | null;
  recommendations: Recommendation[];
}


export function useRecommendations(): UseRecommendationsResult {
  const [recommendations] =
    useState<Recommendation[]>([]);

  const [loading] =
    useState(false);

  const [error] =
    useState<Error | null>(null);


  return useMemo(
    () => ({
      loading,
      error,
      recommendations,
    }),
    [
      loading,
      error,
      recommendations,
    ],
  );
}