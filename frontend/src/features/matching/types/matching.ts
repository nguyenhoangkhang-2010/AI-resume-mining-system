export interface MatchResult {
  id: string;

  candidateName: string;

  position: string;

  score: number;

  skills: string[];

  summary?: string;
}