import {
  useQuery,
} from "@tanstack/react-query";


import {
  matchCandidates,
} from "@/services/matching.service";


export function useMatching(
  jobId?: string,
){
  const query =
    useQuery({
      queryKey:[
        "matches",
        jobId,
      ],
      queryFn:
        () =>
          matchCandidates(
            jobId!,
          ),
      enabled:
        Boolean(jobId),
    });


  return {
    matches:
      query.data ?? [],
    loading:
      query.isLoading,
    error:
      query.error,
  };
}