import type { components } from "./schema";

type Schemas = components["schemas"];

export type ResumeResponse = Schemas["ResumeResponse"];
export type ResumeStatus = Schemas["ResumeStatusResponse"];
export type ResumeListItem = Schemas["ResumeListItem"];
export type Confidence = Schemas["ConfidenceInfo"];
export type JobSummary = Schemas["JobSummary"];
export type JobDetail = Schemas["JobResponse"];
export type JobCreate = Schemas["JobCreateRequest"];
export type Match = Schemas["MatchResponse"];
export type RankedCandidate = Schemas["RankedCandidate"];
export type JobMatches = Schemas["JobMatchResponse"];
export type JobMatch = Schemas["JobMatch"];
export type ScoreBreakdown = Schemas["ScoreBreakdown"];
export type CandidateSummary = Schemas["CandidateSummary"];
export type SearchResponse = Schemas["CandidateSearchResponse"];
export type ResumePage = Schemas["Page_ResumeListItem_"];
export type JobPage = Schemas["Page_JobSummary_"];

/** The states a resume goes through; the last three are final. */
export const FINAL_STATES = ["processed", "needs_review", "failed"] as const;

export function isFinal(status: string): boolean {
  return (FINAL_STATES as readonly string[]).includes(status);
}

export interface Readiness {
  status: string;
  database?: string;
  models?: string;
  worker?: string;
}

/** Everything the screens need from a backend, live or recorded. */
export interface Api {
  mode: "live" | "demo";
  ready(): Promise<Readiness>;
  uploadResume(file: File): Promise<ResumeResponse>;
  resumeStatus(id: string): Promise<ResumeStatus>;
  listResumes(): Promise<ResumePage>;
  jobsForResume(id: string): Promise<JobMatches>;
  createJob(body: JobCreate): Promise<JobDetail>;
  listJobs(): Promise<JobPage>;
  matchCandidates(jobId: string): Promise<Match>;
  searchCandidates(query: string): Promise<SearchResponse>;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly retryAfter?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
