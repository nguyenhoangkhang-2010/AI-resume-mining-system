import { useMemo } from "react";

import type {
  Job,
  JobSearchParams,
} from "../types/job";


interface UseJobsResult {
  loading: boolean;

  error: Error | null;

  jobs: Job[];

  total: number;

  search: (
    params?: JobSearchParams,
  ) => void;
}


export function useJobs(): UseJobsResult {
  return useMemo(
    () => ({
      loading: false,

      error: null,

      jobs: [],

      total: 0,

      search: () => {},
    }),
    [],
  );
}