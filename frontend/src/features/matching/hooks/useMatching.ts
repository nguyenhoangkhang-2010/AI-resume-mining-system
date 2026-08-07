import {
    useQuery
} from "@tanstack/react-query";


import {
    matchCandidates
} from "@/services/matching.service";


export function useMatching(
    jobId?:string
){

    return useQuery({
        queryKey:[
            "matches",
            jobId
        ],
        queryFn:
            ()=>matchCandidates(
                jobId!
            ),
        enabled:
            Boolean(jobId)
    });
}