import api from "./api";

import type {
    MatchResponse
} from "@/types/matching";


export async function matchCandidates(
    jobId:string
):Promise<MatchResponse>{
    const response =
        await api.get<MatchResponse>(
            `/matches/${jobId}`
        );
    return response.data;
}