export interface RankingResult {
  id: string;

  rank: number;

  candidateName: string;

  position: string;

  score: number;

  summary?: string;
}