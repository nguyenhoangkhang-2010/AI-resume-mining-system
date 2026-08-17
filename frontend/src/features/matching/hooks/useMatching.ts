import { useQuery } from "@tanstack/react-query";

import { matchCandidates } from "@/services/matching.service";

export function useMatching(jobId?: string) {
  const query = useQuery({
    queryKey: ["matches", jobId],
    queryFn: () => matchCandidates(jobId as string),
    enabled: Boolean(jobId),
  });

  return {
    data: query.data,
    matches: query.data?.results ?? [],
    loading: query.isLoading,
    error: query.error,
    jobId: query.data?.job_id,
    metadata: query.data?.metadata,
    refetch: query.refetch,
  };
}