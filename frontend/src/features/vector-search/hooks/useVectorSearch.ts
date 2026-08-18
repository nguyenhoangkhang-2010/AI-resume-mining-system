import { useMemo, useState } from "react";

import type { VectorSearchResult } from "../types/vectorSearch";


interface UseVectorSearchResult {
  loading: boolean;

  error: Error | null;

  results: VectorSearchResult[];

  search: (query: string) => void;
}


export function useVectorSearch(): UseVectorSearchResult {
  const [results] =
    useState<VectorSearchResult[]>([]);

  const [loading] =
    useState(false);

  const [error] =
    useState<Error | null>(null);


  const search = (
    _query: string,
  ) => {
    /*
      Future integration:

      query
        |
        v
      API
        |
        v
      embedding service
        |
        v
      vector database retrieval
    */
  };


  return useMemo(
    () => ({
      loading,
      error,
      results,
      search,
    }),
    [
      loading,
      error,
      results,
    ],
  );
}