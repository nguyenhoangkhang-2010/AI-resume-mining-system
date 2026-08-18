export interface Job {
  id: string;
  title: string;
  company?: string;
  location?: string;
  description?: string;
  skills?: string[];
  employmentType?: string;
  experienceLevel?: string;
  salary?: {
    min?: number;
    max?: number;
    currency?: string;
  };
  metadata?: Record<string, unknown>;
}


export interface JobSearchParams {
  query?: string;
  location?: string;
  skills?: string[];
  filters?: Record<string, unknown>;
}


export interface JobsResponse {
  items: Job[];
  total: number;
}