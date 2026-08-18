import { useMemo } from "react";

import type { DashboardData } from "../types/dashboard";

interface UseDashboardResult {
  loading: boolean;
  error: Error | null;
  data: DashboardData | null;
}

export function useDashboard(): UseDashboardResult {
  return useMemo(
    () => ({
      loading: false,
      error: null,
      data: null,
    }),
    [],
  );
}