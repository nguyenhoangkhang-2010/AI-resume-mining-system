import { useMemo, useState } from "react";

import type { RankingResult } from "../types/ranking";


interface UseRankingResult {
  loading: boolean;
  error: Error | null;
  rankings: RankingResult[];
}


export function useRanking(): UseRankingResult {
  const [rankings] =
    useState<RankingResult[]>([]);

  const [loading] =
    useState(false);

  const [error] =
    useState<Error | null>(null);


  return useMemo(
    () => ({
      loading,
      error,
      rankings,
    }),
    [
      loading,
      error,
      rankings,
    ],
  );
}