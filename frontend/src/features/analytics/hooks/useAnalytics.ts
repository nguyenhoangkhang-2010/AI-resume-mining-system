import { useMemo } from "react";

import type {
  AnalyticsData,
} from "../types/analytics";

interface UseAnalyticsResult {
  loading: boolean;
  error: Error | null;
  data: AnalyticsData | null;
}

export function useAnalytics(): UseAnalyticsResult {
  return useMemo(
    () => ({
      loading: false,
      error: null,
      data: {
        stats: [],
        charts: [],
      },
    }),
    [],
  );
}