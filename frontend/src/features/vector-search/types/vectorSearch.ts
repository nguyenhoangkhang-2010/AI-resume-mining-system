export interface VectorSearchResult {
  id: string;

  title: string;

  type: string;

  similarity: number;

  description: string;

  tags: string[];
}