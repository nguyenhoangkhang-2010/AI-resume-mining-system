import { useMemo, useState } from "react";

import type { MatchResult } from "../types/matching";


interface UseMatchingResult {
  loading: boolean;
  error: Error | null;
  matches: MatchResult[];
}


export function useMatching(): UseMatchingResult {
  const [matches] =
    useState<MatchResult[]>([]);

  const [loading] =
    useState(false);

  const [error] =
    useState<Error | null>(null);


  return useMemo(
    () => ({
      loading,
      error,
      matches,
    }),
    [
      loading,
      error,
      matches,
    ],
  );
}