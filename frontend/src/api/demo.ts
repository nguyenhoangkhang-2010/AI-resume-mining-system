import fixtures from "../demo/fixtures.json";
import {
  ApiError,
  type Api,
  type JobMatches,
  type JobPage,
  type Match,
  type ResumePage,
  type ResumeStatus,
  type SearchResponse,
} from "./types";

/**
 * The recorded demo: answers captured from the real API running on synthetic
 * data (scripts/make_demo_fixtures.py), replayed with no server. It lets the
 * interface be tried without the models, MongoDB or a key.
 */
interface Sample {
  id: string;
  label: string;
  description: string;
  filename: string;
  status: ResumeStatus;
  jobs: JobMatches | null;
}

interface Fixtures {
  generated: string;
  jobs: JobPage;
  matches: Record<string, Match>;
  searches: Record<string, SearchResponse>;
  resumes: ResumePage;
  samples: Sample[];
}

const data = fixtures as unknown as Fixtures;

export const SAMPLE_CVS = data.samples.map(({ id, label, description, filename }) => ({
  id,
  label,
  description,
  filename,
}));

export const PRESET_QUERIES = Object.keys(data.searches);

// Pending, then processing, then the recorded result: what a real upload looks like.
const PENDING_MS = 500;
const PROCESSING_MS = 1500;

export function demoApi(now: () => number = Date.now): Api {
  const started = new Map<string, number>();

  const sample = (id: string): Sample => {
    const found = data.samples.find((entry) => entry.id === id);

    if (!found) throw new ApiError(404, "not_found", "Unknown sample CV");

    return found;
  };

  return {
    mode: "demo",
    ready: async () => ({ status: "ready", database: "recorded", models: "recorded", worker: "n/a" }),

    uploadResume: async (file) => {
      const match = data.samples.find((entry) => entry.filename === file.name);

      if (!match) throw new ApiError(400, "invalid_upload", "The demo only knows its sample CVs.");

      started.set(match.id, now());

      return {
        id: match.id,
        filename: match.filename,
        upload_status: "pending",
        created_at: new Date(now()).toISOString(),
      };
    },

    resumeStatus: async (id) => {
      const entry = sample(id);
      const elapsed = now() - (started.get(id) ?? 0);

      if (elapsed < PENDING_MS) return { resume_id: id, status: "pending" };
      if (elapsed < PROCESSING_MS) return { resume_id: id, status: "processing" };

      return entry.status;
    },

    listResumes: async () => data.resumes,

    jobsForResume: async (id) => {
      const entry = sample(id);

      if (!entry.jobs) throw new ApiError(409, "conflict", "This CV was not turned into a candidate.");

      return entry.jobs;
    },

    createJob: async () => {
      throw new ApiError(0, "demo", "Creating a job needs the live API (it reads the description with a model).");
    },

    listJobs: async () => data.jobs,

    matchCandidates: async (jobId) => {
      const found = data.matches[jobId];

      if (!found) throw new ApiError(404, "not_found", "Job not in the recorded demo");

      return found;
    },

    searchCandidates: async (query) => data.searches[query] ?? { query, results: [] },
  };
}
