import { ApiError, type Api, type Readiness } from "./types";

export interface ConnectionSettings {
  /** Empty means the page's own origin (the dev server proxies /api). */
  baseUrl: string;
  apiKey: string;
}

export function liveApi(settings: () => ConnectionSettings): Api {
  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const { baseUrl, apiKey } = settings();
    const headers = new Headers(init.headers);

    if (apiKey) headers.set("X-API-Key", apiKey);
    if (typeof init.body === "string") headers.set("Content-Type", "application/json");

    let response: Response;

    try {
      response = await fetch(baseUrl.replace(/\/$/, "") + path, { ...init, headers });
    } catch {
      throw new ApiError(
        0,
        "unreachable",
        "The API cannot be reached. Is it running, and is the address right?",
      );
    }

    if (!response.ok) {
      let code = "error";
      let detail = response.statusText || "Request failed";

      try {
        const body = await response.json();
        code = body.code ?? code;
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? detail);
      } catch {
        // not JSON: keep the status text
      }

      const retry = Number(response.headers.get("Retry-After"));
      throw new ApiError(response.status, code, detail, retry > 0 ? retry : undefined);
    }

    return (await response.json()) as T;
  }

  return {
    mode: "live",
    ready: async () => {
      // /ready answers 503 with a body while the API is starting.
      const { baseUrl } = settings();
      const response = await fetch(baseUrl.replace(/\/$/, "") + "/ready").catch(() => null);

      if (!response) throw new ApiError(0, "unreachable", "The API cannot be reached.");

      return (await response.json()) as Readiness;
    },
    uploadResume: (file) => {
      const form = new FormData();
      form.append("file", file);

      return request("/api/v1/resumes/upload", { method: "POST", body: form });
    },
    resumeStatus: (id) => request(`/api/v1/resumes/${id}/status`),
    listResumes: () => request("/api/v1/resumes/?limit=50"),
    jobsForResume: (id) => request(`/api/v1/resumes/${id}/jobs?top_k=8`),
    createJob: (body) => request("/api/v1/jobs/", { method: "POST", body: JSON.stringify(body) }),
    listJobs: () => request("/api/v1/jobs/?limit=50"),
    matchCandidates: (jobId) => request(`/api/v1/matches/${jobId}`),
    searchCandidates: (query) =>
      request("/api/v1/search/candidates", {
        method: "POST",
        body: JSON.stringify({ query, top_k: 10 }),
      }),
  };
}
