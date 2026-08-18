export interface CandidateProfile {

    id:string;

    resume_id:string;

    personal_info:Record<string, unknown>;

    education:Array<Record<string, unknown>>;

    experience:Array<Record<string, unknown>>;

    skills:string[];

}


export interface RankedCandidate {

    similarity_score:number;

    skill_gaps:string[];

    candidate_profile:CandidateProfile;

}


export interface RankingMetadata {

    total_candidates:number;

    ranked_candidates:number;

    filtered_candidates:number;

    similarity_threshold:number;

}


export interface MatchResponse {

    job_id:string;

    results:RankedCandidate[];

    metadata:RankingMetadata;

}